"""Phase 3 acceptance: visibility leak test, scripture filtering, fusion, keyword path."""
import json
import os
import uuid

import pytest

os.environ["SHEPHERD_EMBEDDER"] = "fake"
os.environ["SHEPHERD_RERANKER"] = "fake"

from shepherd import config  # noqa: E402
from shepherd.embed import get_embedder  # noqa: E402
from shepherd.retrieve import (  # noqa: E402
    keyword_candidates, retrieve, rrf, scripture_candidates, vector_candidates, visibility_clause,
)
from pgvector.psycopg import register_vector  # noqa: E402

LEADER_TEXT = "Leaders only: the secret discipline of the inner council. Romans 8:28 applies."
MEMBER_TEXT = "For everyone: rejoice in hope, be patient in tribulation. Romans 12:12 and John 3:16."
MEMBER_TEXT_2 = "Open teaching on prayer and fasting from Matthew 6:16, freely shared."


@pytest.fixture
def corpus(admin):
    """One leader-only source and one member source, each with chunks and embeddings."""
    emb = get_embedder()
    register_vector(admin)

    def add_source(title, visibility, status="ready"):
        return admin.execute(
            "insert into sources (title, author, file_uri, visibility, status) values (%s, 'T', 's3://x/t', %s, %s) returning id",
            (title, visibility, status),
        ).fetchone()[0]

    def add_chunk(sid, text, chapter=1):
        from shepherd.scripture import extract_verse_ids
        return admin.execute(
            f"insert into chunks (source_id, content, raw_content, {config.EMBED_COLUMN}, location, scripture) "
            "values (%s, %s, %s, %s, %s, %s) returning id::text",
            (sid, text, text, emb.embed([text])[0], json.dumps({"chapter": chapter}), extract_verse_ids(text)),
        ).fetchone()[0]

    leader = add_source("Leader Book", "leader")
    member = add_source("Member Book", "member")
    pending = add_source("Unfinished Book", "member", status="pending")
    ids = {
        "leader_chunk": add_chunk(leader, LEADER_TEXT),
        "member_chunk": add_chunk(member, MEMBER_TEXT),
        "member_chunk_2": add_chunk(member, MEMBER_TEXT_2, chapter=2),
        "pending_chunk": add_chunk(pending, "pending text inner council Romans 8:28"),
    }
    # the queue must be empty for other tests; this pending row is deleted by isolate_sources
    return {"leader": leader, "member": member, **ids}


def ids_of(rows):
    return {r[0] for r in rows}


def test_visibility_clause_fails_closed_for_unknown_role():
    assert "visibility = 'member'" in visibility_clause("member")
    assert "visibility = 'member'" in visibility_clause("guest")
    assert "visibility" not in visibility_clause("leader")


def test_member_never_sees_leader_chunks_on_any_path(app, corpus):
    """The leak test. Every candidate path is checked independently, then the full pipeline."""
    emb = get_embedder()
    register_vector(app)
    q = "secret discipline of the inner council"
    qvec = emb.embed([LEADER_TEXT])[0]  # the leader chunk's own vector: nearest possible match
    leader_id = corpus["leader_chunk"]

    with app.transaction():
        assert leader_id not in ids_of(vector_candidates(app, qvec, "member", []))
        assert leader_id not in ids_of(keyword_candidates(app, q, "member", []))
        assert leader_id not in ids_of(scripture_candidates(app, "member", [45008028]))
        # and a leader does see it on each path
        assert leader_id in ids_of(vector_candidates(app, qvec, "leader", []))
        assert leader_id in ids_of(keyword_candidates(app, q, "leader", []))
        assert leader_id in ids_of(scripture_candidates(app, "leader", [45008028]))

    got = retrieve(app, q, role="member")
    assert all(p.source_id != str(corpus["leader"]) for p in got)
    got = retrieve(app, q, role="leader")
    assert any(p.chunk_id == leader_id for p in got)


def test_pending_sources_are_never_retrieved(app, corpus):
    got = retrieve(app, "inner council", role="leader")
    assert corpus["pending_chunk"] not in {p.chunk_id for p in got}


def test_keyword_path_finds_exact_words(app, corpus):
    # the dev DB may hold real books that also use the word; assert membership, not equality
    with app.transaction():
        rows = keyword_candidates(app, "tribulation", "leader", [])
    assert corpus["member_chunk"] in ids_of(rows)
    assert corpus["leader_chunk"] not in ids_of(rows)


def test_scripture_verse_query_puts_citing_passages_first(app, corpus):
    got = retrieve(app, "What do we teach on John 3:16 about tribulation?", role="leader")
    assert got[0].chunk_id == corpus["member_chunk"]            # cites the verse: first, whatever the reranker said
    cites = [43003016 in p.scripture for p in got]
    assert cites == sorted(cites, reverse=True)                 # citing passages, then the top-up
    assert corpus["member_chunk_2"] in {p.chunk_id for p in got}   # soft: a thin verse pool is topped up


def test_hard_scripture_filter_keeps_only_citing_passages(app, corpus, monkeypatch):
    import shepherd.retrieve as R
    monkeypatch.setattr(R, "SCRIPTURE_FILTER", "hard")
    got = retrieve(app, "What do we teach on John 3:16 about tribulation?", role="leader")
    assert got and all(43003016 in p.scripture for p in got)
    assert corpus["member_chunk_2"] not in {p.chunk_id for p in got}


def test_scripture_chapter_range_query(app, corpus):
    got = retrieve(app, "Romans 8 secret discipline", role="leader")
    assert got[0].chunk_id == corpus["leader_chunk"]            # cites Romans 8:28
    in_ch8 = [any(45008001 <= v <= 45008999 for v in p.scripture) for p in got]
    assert in_ch8 == sorted(in_ch8, reverse=True)


def test_scripture_filter_respects_visibility(app, corpus):
    got = retrieve(app, "Romans 8 secret discipline", role="member")
    assert corpus["leader_chunk"] not in {p.chunk_id for p in got}
    assert all(p.source_id != str(corpus["leader"]) for p in got)


def test_rrf_prefers_items_on_both_lists():
    a = ("a", "s", "T", None, {}, "a text", [])
    b = ("b", "s", "T", None, {}, "b text", [])
    c = ("c", "s", "T", None, {}, "c text", [])
    fused = rrf({"vector": [a, b], "keyword": [c, a]})
    assert [p.chunk_id for p in fused][0] == "a"
    assert fused[0].rank_sources == {"vector": 1, "keyword": 2}


def test_final_k_is_respected(app, corpus):
    assert len(retrieve(app, "hope prayer council", role="leader", final_k=1)) == 1


def test_keyword_path_does_not_require_every_word(app, corpus):
    """A natural question with words absent from the passage must still match on the rest."""
    # k is large because real books in the dev DB also match some of these words
    with app.transaction():
        rows = keyword_candidates(app, "what happens to a believer in tribulation", "leader", [], k=500)
    assert corpus["member_chunk"] in ids_of(rows)


def test_keyword_ranking_rewards_more_matches(app, corpus):
    with app.transaction():
        rows = keyword_candidates(app, "rejoice hope patient tribulation", "leader", [])
    top5 = [r[0] for r in rows[:5]]
    assert corpus["member_chunk"] in top5          # matches all four words
    assert corpus["member_chunk_2"] not in ids_of(rows)   # matches none


# --- named books (stage 6) ---------------------------------------------------------------

from shepherd.retrieve import named_books, names_title, title_forms  # noqa: E402

TITLES = ["Loyalty and Disloyalty", "Others", "The Secret", "Backsliding", "How to Pray", "Church Growth",
          "Poison: Taming The Tongue", "The Art of Leadership - 3rd Edition", "WOM14. The Tests of the Righteous",
          "Those Who Are Offended"]


def _named(q):
    return [t for t in TITLES if any(names_title(q, w) for w in title_forms(t))]


@pytest.mark.parametrize("q,book", [
    ("What does Loyalty and Disloyalty say about stages?", "Loyalty and Disloyalty"),
    ("In the book Backsliding, what are the signs?", "Backsliding"),
    ("According to Church Growth, why do churches stop growing?", "Church Growth"),
    ("What does *Poison* say about gossip?", "Poison: Taming The Tongue"),
    ("What does The Art of Leadership say about delegation?", "The Art of Leadership - 3rd Edition"),
    ("In The Tests of the Righteous, why do tests come?", "WOM14. The Tests of the Righteous"),
    ("What does “The Secret” teach?", "The Secret"),
])
def test_a_named_book_is_recognised(q, book):
    assert _named(q) == [book]


@pytest.mark.parametrize("q", [
    "How can I encourage others who are going through hard times?",
    "What is the secret to answered prayer?",
    "How to pray for my family?",
    "How do I help those who are offended?",
    "How can we have church growth in a village?",
    "Backsliding: how does it start?",          # one word at the start of a sentence is not a title
])
def test_everyday_words_are_not_a_book(q):
    assert _named(q) == []


def test_named_book_restricts_search(app, corpus):
    with app.transaction():
        assert named_books(app, "What does 'Member Book' say about hope?", "member") == [str(corpus["member"])]
        assert named_books(app, "What does 'Leader Book' say?", "member") == []      # invisible to members
    got = retrieve(app, "What does 'Member Book' say about patience in tribulation?", role="leader")
    assert got and {p.source_id for p in got} == {str(corpus["member"])}


# --- merging neighbours (stage 5) ----------------------------------------------------------

from shepherd.retrieve import Passage, _join, merge_neighbours  # noqa: E402


def _p(cid, chunk, text, book="b", chapter=1, score=0.0, verses=()):
    return Passage(chunk_id=cid, source_id=book, title="T", author=None, location={"chapter": chapter, "chunk": chunk},
                   raw_content=text, scripture=list(verses), score=score)


def test_join_drops_the_carried_overlap():
    a = "Para one.\n\nPara two.\n\nShared tail para."
    b = "Shared tail para.\n\nPara four."
    assert _join(a, b) == "Para one.\n\nPara two.\n\nShared tail para.\n\nPara four."
    assert _join("x", "y") == "x\n\ny"               # no overlap: plain join


def test_neighbours_merge_in_reading_order_and_free_a_slot():
    ranked = [_p("c5", 5, "five.\n\nshared", verses=[1]), _p("other", 0, "elsewhere", book="z"),
              _p("c4", 4, "four.\n\nfive.", verses=[2]), _p("next", 9, "later")]
    out = merge_neighbours(ranked, final_k=3)
    assert [p.chunk_id for p in out] == ["c4", "other", "next"]      # the merged passage starts at chunk 4
    merged = out[0]
    assert merged.raw_content == "four.\n\nfive.\n\nshared" and merged.chunk_ids == ["c4", "c5"]
    assert merged.scripture == [1, 2]


def test_merge_respects_chapter_and_cap():
    ranked = [_p("a", 1, "a"), _p("b", 2, "b", chapter=2), _p("c", 2, "c"), _p("d", 3, "d"), _p("e", 4, "e")]
    out = merge_neighbours(ranked, final_k=8)
    assert [p.chunk_ids for p in out] == [["a", "c", "d"], ["b"], ["e"]]   # chapter 2's chunk 2 stays apart; cap of 3
