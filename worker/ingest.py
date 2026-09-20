"""Book file -> parse -> chunk -> enrich -> scripture -> embed -> store.

`process_source` runs entirely inside one transaction, so a failure part-way
leaves no half-ingested chunks. Re-ingestion is handled here too: when the new
source's meta carries `replaces`, the old source is marked superseded and its
chunks deleted in the same transaction.
"""
from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

from shepherd import config, storage
from shepherd.chunking import chunk_text
from shepherd.db import connect, transaction
from shepherd.embed import Embedder, get_embedder
from shepherd.enrich import context_header, enrich
from shepherd.scripture import extract_verse_ids

from .parsers import ParsedBook
from .parsers.epub import parse_epub

log = logging.getLogger("worker.ingest")

PARSERS = {".epub": parse_epub}
EMBED_SLICE = 64     # chunks embedded per progress report


def fingerprint(content: str) -> str:
    """Same text + same embedding model => the old embedding (and questions) can be reused."""
    return hashlib.sha256(f"{config.EMBED_MODEL}\n{content}".encode()).hexdigest()


def report(source_id, message: str) -> None:
    """Progress the admin page can see while the ingest transaction is open (own connection)."""
    try:
        with connect() as c, c.transaction():
            c.execute("insert into ingest_progress (source_id, message) values (%s, %s) "
                      "on conflict (source_id) do update set message = excluded.message, updated_at = now()",
                      (source_id, message))
    except Exception as e:  # noqa: BLE001 - progress is cosmetic; never fail an ingest over it
        log.warning("progress for %s not written: %s", source_id, e)


def reusable(conn, old_id, prints: list[str]) -> dict:
    """fingerprint -> (embedding, questions, q_embedding) from the version being replaced."""
    if not old_id:
        return {}
    rows = conn.execute(
        "select fingerprint, embedding, questions, q_embedding from chunks "
        "where source_id = %s and fingerprint = any(%s)", (old_id, prints)).fetchall()
    return {r[0]: r[1:] for r in rows}


class UnsupportedFormat(Exception):
    pass


def parse_file(path: Path) -> ParsedBook:
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        raise UnsupportedFormat(f"no parser for {path.suffix!r}")
    return parser(path)


def build_chunks(src: dict, book: ParsedBook, embedder: Embedder) -> list[dict]:
    title = src["title"] or book.title or "Untitled"
    author = src["author"] or book.author
    rows: list[dict] = []
    for sec in book.sections:
        header = context_header(title, author, src["series"], sec.chapter, sec.title)
        for c in chunk_text(sec.text, count=embedder.count_tokens):
            loc = {"chapter": sec.chapter, "title": sec.title, "page": sec.page, "chunk": c.index}
            rows.append(
                {
                    "raw_content": c.text,
                    "content": enrich(c.text, header),
                    "location": loc,
                    "scripture": extract_verse_ids(c.text),
                    "token_count": c.token_count,
                }
            )
    if not rows:
        raise ValueError("parsed book produced no text")
    return rows


def process_source(conn: psycopg.Connection, source_id, embedder: Embedder | None = None) -> int:
    """Ingest one source. Returns the number of chunks written. Raises on failure."""
    embedder = embedder or get_embedder()
    register_vector(conn)
    with transaction(conn):
        src = conn.execute(
            "select id, title, author, series, file_uri, meta from sources where id = %s for no key update",
            (source_id,),
        ).fetchone()
        if src is None:
            raise LookupError(f"source {source_id} not found")
        src = dict(zip(["id", "title", "author", "series", "file_uri", "meta"], src))

        with tempfile.TemporaryDirectory() as tmp:
            local = storage.download(src["file_uri"], Path(tmp))
            book = parse_file(local)

        report(source_id, "parsed, splitting into passages")
        rows = build_chunks(src, book, embedder)
        old_id = (src["meta"] or {}).get("replaces")
        prints = [fingerprint(r["content"]) for r in rows]
        old = reusable(conn, old_id, prints)
        todo = [i for i, fp in enumerate(prints) if fp not in old]
        vectors: list = [old[fp][0] if fp in old else None for fp in prints]
        for start in range(0, len(todo), EMBED_SLICE):
            report(source_id, f"embedding {start}/{len(todo)}" + (f" ({len(old)} reused)" if old else ""))
            batch = todo[start:start + EMBED_SLICE]
            for i, v in zip(batch, embedder.embed([rows[i]["content"] for i in batch])):
                vectors[i] = v
        report(source_id, "saving")

        with conn.cursor() as cur:
            cur.executemany(
                "insert into chunks (source_id, content, raw_content, embedding, location, scripture, token_count, "
                " fingerprint, questions, q_embedding) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (source_id, r["content"], r["raw_content"], v, json.dumps(r["location"]), r["scripture"],
                     r["token_count"], fp, *(old[fp][1:] if fp in old else (None, None)))
                    for r, v, fp in zip(rows, vectors, prints)
                ],
            )

        # fill metadata the file told us, if the upload didn't
        conn.execute(
            "update sources set title = coalesce(nullif(title, ''), %s), author = coalesce(author, %s), "
            " status = 'ready', failure_reason = null where id = %s",
            (book.title or src["title"], book.author, source_id),
        )

        if old_id:
            conn.execute("delete from chunks where source_id = %s", (old_id,))
            conn.execute(
                "update sources set status = 'superseded', superseded_by = %s where id = %s",
                (source_id, old_id),
            )
    with transaction(conn):
        conn.execute("delete from ingest_progress where source_id = %s", (source_id,))
    return len(rows)


def mark_failed(conn: psycopg.Connection, source_id, reason: str) -> None:
    with transaction(conn):
        conn.execute(
            "update sources set status = 'failed', failure_reason = %s where id = %s",
            (reason[:2000], source_id),
        )
        conn.execute("delete from ingest_progress where source_id = %s", (source_id,))


def enqueue_reingest(conn: psycopg.Connection, source_id) -> str:
    """Create a new pending version of a source. Returns the new source id."""
    with transaction(conn):
        old = conn.execute(
            "select title, author, series, date, visibility, file_uri, version, meta "
            "from sources where id = %s and status in ('ready', 'failed')",
            (source_id,),
        ).fetchone()
        if old is None:
            raise LookupError("source not found or not re-ingestable")
        title, author, series, date, visibility, file_uri, version, meta = old
        meta = dict(meta or {})
        meta["replaces"] = str(source_id)
        new_id = conn.execute(
            "insert into sources (title, author, series, date, visibility, file_uri, "
            " version, meta) values (%s, %s, %s, %s, %s, %s, %s, %s) returning id",
            (title, author, series, date, visibility, file_uri, version + 1, json.dumps(meta)),
        ).fetchone()[0]
    return str(new_id)


def add_book(conn, path: Path, title: str | None, author: str | None, series: str | None, visibility: str = "member") -> str:
    """Upload a book file and queue it for ingestion. Returns the new source id."""
    import uuid

    sid = uuid.uuid4()
    storage.ensure_bucket()
    uri = storage.upload_book(str(sid), path)
    with transaction(conn):
        conn.execute(
            "insert into sources (id, title, author, series, visibility, file_uri) values (%s, %s, %s, %s, %s, %s)",
            (sid, title or path.stem, author, series, visibility, uri),
        )
    return str(sid)
