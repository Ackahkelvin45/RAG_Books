"""Hybrid retrieval: vector + keyword + generated-questions vector (+ scripture filter) -> RRF -> rerank.

Visibility is enforced inside the SQL of every candidate query, never as a
post-filter: a member-role request can only ever see sources whose visibility
is 'member'. Leaders and admins see everything. Only 'ready' sources count.

    python -m shepherd.retrieve "what does Bunyan say about despair" [--role member]
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field

import psycopg
from pgvector.psycopg import register_vector

from . import config
from .embed import get_embedder
from .rerank import get_reranker
from .scripture import extract_verse_ids

# how many candidates each leg contributes before fusion; widen them to trade CPU for recall
VECTOR_K = int(os.environ.get("SHEPHERD_VECTOR_K", "30"))
KEYWORD_K = int(os.environ.get("SHEPHERD_KEYWORD_K", "30"))
RERANK_POOL = config.RERANK_POOL
FINAL_K = 8
RRF_K = 60
# stage 4: also match the question against each chunk's generated questions (on: SHEPHERD_QUESTION_SEARCH=on).
# Off by default: eval 2026-09-19 showed +5 pts on generated questions (biased: same model wrote both) but no gain on
# hand-written ones. Questions keep being generated, so it can be re-tested against real church questions.
# stage 5: fold a result into a higher-ranked neighbour from the same chapter (off: SHEPHERD_MERGE_NEIGHBOURS=off)
MERGE_NEIGHBOURS = os.environ.get("SHEPHERD_MERGE_NEIGHBOURS", "on").lower() != "off"
MERGE_MAX = 3            # chunks per merged passage, so one passage never crowds out the rest
QUESTION_SEARCH = os.environ.get("SHEPHERD_QUESTION_SEARCH", "off").lower() == "on"
# A verse in the question filters every list to passages citing it (scripture is a first-class query). 'soft',
# the default, tops a thin filtered pool up with unfiltered candidates, ranked below the citing ones, so a
# personal question that happens to quote a verse still gets its best passages. 'hard' keeps the filter alone.
SCRIPTURE_FILTER = os.environ.get("SHEPHERD_SCRIPTURE_FILTER", "soft").lower()
KEYWORD_PREFILTER = int(os.environ.get("SHEPHERD_KEYWORD_PREFILTER", "1000"))   # rows ranked by ts_rank_cd before the per-row coverage sort

_ROLE_SEES_LEADER = {"leader": True, "admin": True, "member": False}

# ponytail: one in-process gate. The server has one core, so two searches at once each take twice as long;
# queued, the second waits and both finish sooner. Raise it on a box with cores to spare.
GATE = threading.BoundedSemaphore(int(os.environ.get("SHEPHERD_MAX_CONCURRENT_SEARCHES", "1")))


@dataclass
class Passage:
    chunk_id: str
    source_id: str
    title: str
    author: str | None
    location: dict
    raw_content: str
    scripture: list[int]
    score: float = 0.0
    rank_sources: dict = field(default_factory=dict)  # {"vector": rank, "keyword": rank}
    merged_ids: list = field(default_factory=list)    # neighbours folded into this passage (stage 5)

    @property
    def chunk_ids(self) -> list[str]:
        return [self.chunk_id, *self.merged_ids]


def visibility_clause(role: str) -> str:
    """SQL fragment restricting sources by the caller's role. Fails closed for unknown roles."""
    if _ROLE_SEES_LEADER.get(role, False):
        return "s.status = 'ready'"
    return "s.status = 'ready' and s.visibility = 'member'"


_SELECT = """
select c.id::text, c.source_id::text, s.title, s.author, c.location, c.raw_content, c.scripture
from chunks c join sources s on s.id = c.source_id
"""


def _where(role: str, verse_ids: list[int], book_ids: list[str] | None, extra: str = "") -> tuple[str, list]:
    sql, params = f"where {visibility_clause(role)}{extra}", []
    if verse_ids:
        sql += " and c.scripture && %s::bigint[]"
        params.append(verse_ids)
    if book_ids:
        sql += " and c.source_id = any(%s::uuid[])"
        params.append(book_ids)
    return sql, params


def vector_candidates(conn, qvec, role: str, verse_ids: list[int], k: int = VECTOR_K, book_ids=None) -> list[tuple]:
    # config.EMBED_COLUMN, not a parameter: the column must match the model that made qvec.
    where, params = _where(role, verse_ids, book_ids)
    return conn.execute(_SELECT + where + f" order by c.{config.EMBED_COLUMN} <=> %s::vector limit %s",
                        params + [qvec, k]).fetchall()


def question_candidates(conn, qvec, role: str, verse_ids: list[int], k: int = VECTOR_K, book_ids=None) -> list[tuple]:
    """Chunks whose generated questions are closest in meaning to the user's question."""
    where, params = _where(role, verse_ids, book_ids, " and c.q_embedding is not null")
    return conn.execute(_SELECT + where + " order by c.q_embedding <=> %s::vector limit %s", params + [qvec, k]).fetchall()


# websearch_to_tsquery ANDs every non-stop word, so a natural question such as
# "what happens to Christian at Vanity Fair" demands "happen" too and misses the
# chunks about Vanity Fair. OR the terms instead and let ts_rank_cd reward chunks
# that match more of them. Quoted phrases keep their <-> proximity operator.
_TSQUERY = "to_tsquery('english', replace(websearch_to_tsquery('english', %s)::text, ' & ', ' | '))"
_COVERAGE = (
    "cardinality(array(select unnest(tsvector_to_array(c.ts_doc)) "
    "intersect select unnest(tsvector_to_array(to_tsvector('english', %s)))))"
)


def keyword_candidates(conn, query: str, role: str, verse_ids: list[int], k: int = KEYWORD_K, book_ids=None) -> list[tuple]:
    # Rank by how many distinct query terms the chunk covers, then by ts_rank_cd, so one passage matching every
    # term beats a long one repeating a single term. The coverage sort is a set intersection per row, so it runs
    # over the KEYWORD_PREFILTER best rows by ts_rank_cd only: an ordinary question OR-matches most of the library
    # (8,045 of 13,843 chunks) and the per-row subquery over all of them was the slowest SQL in a search.
    where, params = _where(role, verse_ids, book_ids, f" and c.ts_doc @@ {_TSQUERY}")
    inner = (f"select c.id::text, c.source_id::text, s.title, s.author, c.location, c.raw_content, c.scripture, c.ts_doc "
             f"from chunks c join sources s on s.id = c.source_id {where} "
             f"order by ts_rank_cd(c.ts_doc, {_TSQUERY}) desc limit %s")
    sql = (f"select id, source_id, title, author, location, raw_content, scripture from ({inner}) c "
           f"order by {_COVERAGE} desc, ts_rank_cd(c.ts_doc, {_TSQUERY}) desc limit %s")
    return conn.execute(sql, [query] + params + [query, max(KEYWORD_PREFILTER, k), query, query, k]).fetchall()


def scripture_candidates(conn, role: str, verse_ids: list[int], k: int = VECTOR_K, book_ids=None) -> list[tuple]:
    """Fallback when the query is essentially just a reference and has no other words to match."""
    where, params = _where(role, verse_ids, book_ids)
    return conn.execute(_SELECT + where + " order by c.created_at limit %s", params + [k]).fetchall()


# --- named books (stage 6) ---------------------------------------------------------------
# "What does Loyalty and Disloyalty say about..." searches that book only. Titles that are also everyday
# words ("Others", "The Secret", "How to Pray") need a sign the person means the book.

_SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "is", "it", "of", "on", "or", "the", "to", "with", "you", "your"}
_EDITION = re.compile(r"\([^)]*\)|-?\s*\b\d+(st|nd|rd|th)?\s*(ed|edition)\b|^\s*(wom|ts|pr)\s*\d+\.\s*", re.I)
_OPEN, _CLOSE = "\"'\u201c\u2018*_", "\"'\u201d\u2019*_"
_BEFORE_CUE = re.compile(r"(\bbooks?|\baccording to|\bin the book)[\s:,]*$", re.I)
_AFTER_CUE = re.compile(r"^[\s\"'\u201d\u2019*_]*(says?|teach(es)?)\b", re.I)


def title_forms(title: str) -> list[list[str]]:
    """Word lists a title may be written as: the whole title, and each part around ':' ',' '?' or a line break."""
    base = _EDITION.sub(" ", title)
    forms = []
    for part in [base, *re.split(r"[:,?\n]", base)]:
        words = re.findall(r"[a-z0-9']+", part.lower().replace("\u2019", "'"))
        if words and words[0] == "the":
            words = words[1:]
        if words and words not in forms:
            forms.append(words)
    return forms


def names_title(text: str, words: list[str]) -> bool:
    pattern = r"\b(?:the\s+)?" + r"[^a-z0-9']+".join(map(re.escape, words)) + r"\b"
    for m in re.finditer(pattern, text, re.I):
        before, after = text[: m.start()], text[m.end():]
        quoted = before[-1:] in _OPEN and after[:1] in _CLOSE
        cued = bool(_BEFORE_CUE.search(before) or _AFTER_CUE.match(after))
        found = re.findall(r"[A-Za-z0-9']+", m.group())
        title_case = len(words) >= 2 and all(w[0].isupper() or w.lower() in _SMALL or w[0].isdigit() for w in found)
        if quoted or cued or title_case:   # a lowercase title phrase is just words
            return True
    return False


def named_books(conn, query: str, role: str) -> list[str]:
    """Ids of the visible books the query names by title."""
    rows = conn.execute(f"select s.id::text, s.title from sources s where {visibility_clause(role)}").fetchall()
    text = query.replace("\u2019", "'")
    return [sid for sid, title in rows if any(names_title(text, w) for w in title_forms(title))]


def rrf(ranked_lists: dict[str, list[tuple]], k: int = RRF_K) -> list[Passage]:
    scores: dict[str, float] = defaultdict(float)
    passages: dict[str, Passage] = {}
    for name, rows in ranked_lists.items():
        for rank, row in enumerate(rows, start=1):
            cid = row[0]
            scores[cid] += 1.0 / (k + rank)
            if cid not in passages:
                passages[cid] = Passage(
                    chunk_id=row[0], source_id=row[1], title=row[2], author=row[3],
                    location=row[4], raw_content=row[5], scripture=list(row[6] or []),
                )
            passages[cid].rank_sources[name] = rank
    fused = sorted(passages.values(), key=lambda p: scores[p.chunk_id], reverse=True)
    for p in fused:
        p.score = scores[p.chunk_id]
    return fused


def retrieve(
    conn: psycopg.Connection,
    query: str,
    role: str = "leader",
    final_k: int = FINAL_K,
    embedder=None,
    reranker=None,
    timings: dict | None = None,
) -> list[Passage]:
    """`timings`, when given, receives embed_ms, sql_ms and rerank_ms for query_logs."""
    embedder = embedder or get_embedder()
    reranker = reranker or get_reranker()
    register_vector(conn)
    t = timings if timings is not None else {}
    t0 = time.monotonic()

    verse_ids = extract_verse_ids(query)
    qvec = embedder.embed([query])[0]
    t["embed_ms"], t0 = int((time.monotonic() - t0) * 1000), time.monotonic()

    with conn.transaction():
        books = named_books(conn, query, role)

        def gather(book_ids, verses=verse_ids):
            lists = {
                "vector": vector_candidates(conn, qvec, role, verses, book_ids=book_ids),
                "keyword": keyword_candidates(conn, query, role, verses, book_ids=book_ids),
            }
            if QUESTION_SEARCH:
                lists["questions"] = question_candidates(conn, qvec, role, verses, book_ids=book_ids)
            if verses and not any(lists.values()):
                lists["scripture"] = scripture_candidates(conn, role, verses, book_ids=book_ids)
            return lists

        lists = gather(books or None)
        if books and not any(lists.values()):   # the named book has nothing on it: search everything
            lists = gather(None)
        fused = rrf(lists)[:RERANK_POOL]
        if verse_ids and SCRIPTURE_FILTER != "hard" and len(fused) < RERANK_POOL:
            seen = {p.chunk_id for p in fused}      # top up from the unfiltered search; sorted below the citing ones later
            fused += [p for p in rrf(gather(books or None, [])) if p.chunk_id not in seen][:RERANK_POOL - len(fused)]

    t["sql_ms"], t0 = int((time.monotonic() - t0) * 1000), time.monotonic()
    if not fused:
        t["rerank_ms"] = 0
        return []
    scores = reranker.score(query, [p.raw_content for p in fused])
    t["rerank_ms"] = int((time.monotonic() - t0) * 1000)
    for p, s in zip(fused, scores):
        p.score = s
    fused.sort(key=lambda p: p.score, reverse=True)
    if verse_ids:                                   # passages that cite the verse stay ahead of any top-up
        wanted = set(verse_ids)
        fused.sort(key=lambda p: not (wanted & set(p.scripture)))
    return merge_neighbours(fused, final_k) if MERGE_NEIGHBOURS else fused[:final_k]


def _join(first: str, second: str) -> str:
    """Concatenate adjacent chunks, dropping the overlap the chunker carried from `first` into `second`."""
    head = second.split("\n\n", 1)[0]
    at = first.rfind(head[:200]) if head else -1
    if at > 0 and second.startswith(first[at:]):
        return first[:at] + second
    return first + "\n\n" + second


def merge_neighbours(ranked: list[Passage], final_k: int) -> list[Passage]:
    """Walk results best-first; a chunk next to one already taken (same book, same chapter) is folded into it
    instead of using a slot, and the slot goes to the next result. The merged passage keeps the better rank."""
    out: list[Passage] = []
    spans: dict[int, list] = {}                       # id(passage) -> [(chunk index, text), ...] in reading order
    key = lambda p: (p.source_id, (p.location or {}).get("chapter"))  # noqa: E731
    for p in ranked:
        idx = (p.location or {}).get("chunk")
        host = None
        if idx is not None:
            host = next((o for o in out if key(o) == key(p) and len(spans[id(o)]) < MERGE_MAX
                         and any(abs(i - idx) == 1 for i, _ in spans[id(o)])), None)
        if host is None:
            if len(out) == final_k:
                continue
            out.append(p)
            spans[id(p)] = [(idx, p.raw_content)]
            continue
        span = sorted(spans[id(host)] + [(idx, p.raw_content)])
        spans[id(host)] = span
        text = span[0][1]
        for _, t in span[1:]:
            text = _join(text, t)
        host.raw_content = text
        host.merged_ids.append(p.chunk_id)
        host.scripture = sorted(set(host.scripture) | set(p.scripture))
        first = min(span)[0]                          # cite/read from the first chunk in reading order
        if first == idx:
            host.merged_ids[-1] = host.chunk_id
            host.chunk_id, host.location = p.chunk_id, p.location
    return out


def _main(argv: list[str]) -> int:
    from .db import connect
    from .scripture import format_reference

    if not argv:
        print(__doc__)
        return 2
    role = "member" if "--role" in argv and argv[argv.index("--role") + 1] == "member" else "leader"
    query = " ".join(a for a in argv if not a.startswith("--") and a != "member")
    with connect() as conn:
        for i, p in enumerate(retrieve(conn, query, role=role), start=1):
            loc = p.location or {}
            where = f"ch {loc.get('chapter')}" + (f" p.{loc['page']}" if loc.get("page") else "")
            refs = ", ".join(format_reference(v) for v in p.scripture[:4])
            print(f"\n#{i}  score={p.score:.3f}  {p.title} ({where})  via {p.rank_sources}  [{refs}]")
            print("   " + p.raw_content[:300].replace("\n", " "))
    return 0


if __name__ == "__main__":
    import os

    code = _main(sys.argv[1:])
    sys.stdout.flush()
    os._exit(code)  # torch teardown hang on macOS, see worker/main.py
