"""Phase 2 acceptance: EPUB -> ready, failure -> failed + reason, reingest supersedes."""
import os
import uuid
from pathlib import Path

import pytest
from ebooklib import epub

os.environ["SHEPHERD_EMBEDDER"] = "fake"

from shepherd import storage  # noqa: E402
from shepherd.db import transaction  # noqa: E402
from shepherd.embed import FakeEmbedder  # noqa: E402
from worker.ingest import enqueue_reingest, process_source  # noqa: E402
from worker.main import run_one  # noqa: E402
from worker.parsers.epub import parse_epub  # noqa: E402


def make_epub(path: Path, chapters: int = 3) -> Path:
    book = epub.EpubBook()
    book.set_identifier("test-" + uuid.uuid4().hex)
    book.set_title("A Test Book")
    book.set_language("en")
    book.add_author("Test Author")
    items = []
    for i in range(1, chapters + 1):
        c = epub.EpubHtml(title=f"Chapter {i}", file_name=f"ch{i}.xhtml", lang="en")
        paras = "".join(
            f"<p>Chapter {i} paragraph {j}. Consider Romans {i}:{j} and John 3:16. " + "grace " * 40 + "</p>"
            for j in range(1, 9)
        )
        c.content = f"<html><body><h1>Chapter {i}: Title {i}</h1>{paras}</body></html>"
        book.add_item(c)
        items.append(c)
    book.toc = tuple(items)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *items]
    epub.write_epub(str(path), book)
    return path


def test_parse_epub_yields_chapters(tmp_path):
    p = make_epub(tmp_path / "t.epub", chapters=2)
    parsed = parse_epub(p)
    assert parsed.title == "A Test Book" and parsed.author == "Test Author"
    assert [s.chapter for s in parsed.sections] == [1, 2]
    assert parsed.sections[0].title == "Title 1"
    assert "paragraph 3" in parsed.sections[0].text


def add_source(app, path: Path, title="A Test Book") -> uuid.UUID:
    storage.ensure_bucket()
    sid = uuid.uuid4()
    uri = storage.upload_book(str(sid), path)
    with transaction(app):
        app.execute(
            "insert into sources (id, title, file_uri) values (%s, %s, %s)", (sid, title, uri)
        )
    return sid


def status_and_chunks(app, sid):
    with transaction(app):
        return app.execute(
            "select status, failure_reason, (select count(*) from chunks where source_id = %s) from sources where id = %s",
            (sid, sid),
        ).fetchone()


def test_epub_reaches_ready_with_locations_and_scripture(app, tmp_path):
    sid = add_source(app, make_epub(tmp_path / "book.epub"))
    assert run_one(app) is True
    status, reason, n = status_and_chunks(app, sid)
    assert status == "ready" and reason is None and n >= 3

    with transaction(app):
        rows = app.execute(
            "select location, scripture, content, raw_content, embedding is not null, token_count "
            "from chunks where source_id = %s order by (location->>'chapter')::int, (location->>'chunk')::int",
            (sid,),
        ).fetchall()
    chapters = {r[0]["chapter"] for r in rows}
    assert chapters == {1, 2, 3}
    assert all(43003016 in r[1] for r in rows)          # John 3:16 in every chunk
    assert all(r[2].startswith("From A Test Book by Test Author. Chapter") for r in rows)
    assert all(not r[3].startswith("From A Test Book") for r in rows)  # raw is verbatim
    assert all(r[4] for r in rows) and all(r[5] > 0 for r in rows)


def test_corrupt_file_is_marked_failed_with_reason(app, tmp_path):
    bad = tmp_path / "broken.epub"
    bad.write_bytes(b"this is not a zip file")
    sid = add_source(app, bad, title="Broken")
    assert run_one(app) is True
    status, reason, n = status_and_chunks(app, sid)
    assert status == "failed" and reason and n == 0


def test_unsupported_extension_fails_cleanly(app, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    sid = add_source(app, f)
    run_one(app)
    status, reason, _ = status_and_chunks(app, sid)
    assert status == "failed" and "UnsupportedFormat" in reason


def test_reingest_supersedes_old_version_without_orphans(app, tmp_path):
    sid = add_source(app, make_epub(tmp_path / "v1.epub"))
    run_one(app)
    assert status_and_chunks(app, sid)[0] == "ready"

    new_id = enqueue_reingest(app, sid)
    run_one(app)

    with transaction(app):
        rows = app.execute(
            "select id::text, version, status, superseded_by::text, "
            " (select count(*) from chunks c where c.source_id = s.id) from sources s "
            "where s.id in (%s, %s) order by version",
            (sid, new_id),
        ).fetchall()
        orphans = app.execute(
            "select count(*) from chunks c left join sources s on s.id = c.source_id where s.id is null"
        ).fetchone()[0]
    assert len(rows) == 2
    old, new = rows
    assert old[1] == 1 and old[2] == "superseded" and old[3] == new_id and old[4] == 0
    assert new[0] == new_id and new[1] == 2 and new[2] == "ready" and new[4] > 0
    assert orphans == 0


def test_no_pending_work_returns_false(app):
    assert run_one(app) is False


def test_process_source_leaves_nothing_on_failure(app, tmp_path):
    """A failure mid-ingest rolls back: no chunks, status still recoverable."""
    sid = add_source(app, make_epub(tmp_path / "x.epub"))

    class Boom(FakeEmbedder):
        def embed(self, texts):
            raise RuntimeError("embedding exploded")

    with pytest.raises(RuntimeError):
        process_source(app, sid, embedder=Boom())
    assert status_and_chunks(app, sid)[2] == 0


def test_stale_processing_source_is_requeued(app, admin):
    from worker.main import requeue_stale

    sid = uuid.uuid4()
    # updated_at is set at insert time: the BEFORE UPDATE trigger would overwrite a later backdate
    admin.execute(
        "insert into sources (id, title, file_uri, status, updated_at) "
        "values (%s, 'Stuck', 's3://x/y', 'processing', now() - interval '2 hours')",
        (sid,),
    )
    assert requeue_stale(app) == 1
    assert status_and_chunks(app, sid)[0] == "pending"


def test_recent_processing_source_is_left_alone(app, admin):
    from worker.main import requeue_stale

    sid = uuid.uuid4()
    admin.execute(
        "insert into sources (id, title, file_uri, status) values (%s, 'Busy', 's3://x/y', 'processing')",
        (sid,),
    )
    assert requeue_stale(app) == 0
    assert status_and_chunks(app, sid)[0] == "processing"


def test_front_matter_is_skipped_and_chapters_come_from_text(tmp_path):
    book = epub.EpubBook()
    book.set_identifier("t-" + uuid.uuid4().hex); book.set_title("Real Shape"); book.set_language("en")
    pages = [
        ("copy", "<p>Unless otherwise stated, all Scripture quotations are taken from the King James Version.</p>"),
        ("toc", "<h2>CONTENTS</h2><p>Chapter 1: Why Loyalty?</p><p>Chapter 2: Stages</p>"),
        # long contents pages (100+ chapters) are over the short-section limit but still not prose
        ("toc2", "<p>Contents</p>" + "".join(f"<p>Chapter {i}: A Title For Chapter {i}</p>" for i in range(3, 130))),
        ("c1", "<p>Chapter 1</p><p>Why Loyalty?</p>" + "<p>" + "loyal " * 200 + "</p>"),
        ("c2", "<h2>CHAPTER 2</h2><h3>Stages of Disloyalty</h3>" + "<p>" + "stage " * 200 + "</p>"),
        ("end", "<p>For a complete list of titles by the author visit the site.</p>"),
    ]
    items = []
    for name, html in pages:
        it = epub.EpubHtml(title=name, file_name=f"{name}.xhtml", lang="en")
        it.content = f"<html><body>{html}</body></html>"
        book.add_item(it); items.append(it)
    book.add_item(epub.EpubNcx()); book.add_item(epub.EpubNav()); book.spine = items
    p = tmp_path / "real.epub"; epub.write_epub(str(p), book)
    secs = parse_epub(p).sections
    assert [(s.chapter, s.title) for s in secs] == [(1, "Why Loyalty?"), (2, "Stages of Disloyalty")]


def test_reingest_reuses_unchanged_embeddings_and_questions(app, admin, tmp_path, monkeypatch):
    sid = add_source(app, make_epub(tmp_path / "v1.epub"))
    run_one(app)
    admin.execute("update chunks set questions = 'What is grace?', q_embedding = embedding where source_id = %s", (sid,))
    calls = []
    real = FakeEmbedder.embed
    monkeypatch.setattr(FakeEmbedder, "embed", lambda self, texts: (calls.append(len(texts)), real(self, texts))[1])
    new_id = enqueue_reingest(app, sid)
    run_one(app)
    assert calls == []      # nothing changed: nothing re-embedded
    with transaction(app):
        qs = app.execute("select count(*) filter (where questions = 'What is grace?'), count(*) filter (where q_embedding is not null), "
                         "count(*) from chunks where source_id = %s", (new_id,)).fetchone()
        assert qs[0] == qs[1] == qs[2] > 0
        assert app.execute("select count(*) from ingest_progress").fetchone()[0] == 0   # cleared when done


def test_progress_is_visible_during_ingest(app, tmp_path, monkeypatch):
    from worker import ingest as ing

    seen = []
    monkeypatch.setattr(ing, "report", lambda sid, msg: seen.append(msg))
    sid = add_source(app, make_epub(tmp_path / "v1.epub"))
    run_one(app)
    assert seen[0].startswith("parsed") and any(m.startswith("embedding 0/") for m in seen) and seen[-1] == "saving"
