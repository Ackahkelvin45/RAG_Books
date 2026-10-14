"""Questions each passage answers (improvement stage 4).

DeepSeek writes 3-5 questions per chunk; they are embedded together into chunks.q_embedding,
which retrieve.py searches as a third list. Fills every chunk whose questions are null, a batch
at a time with a commit per batch, so it can be stopped and resumed. The worker calls
`fill_batch` when idle, which covers newly ingested books too.

    python -m shepherd.questions [--limit N]      # backfill the library
"""
from __future__ import annotations

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from pgvector.psycopg import register_vector

from . import config, llm
from .embed import get_embedder

log = logging.getLogger("questions")

BATCH = 64
PARALLEL = 16     # concurrent DeepSeek calls

PROMPT = """You are given one passage from a Christian book. Write 3 to 5 questions that a pastor, shepherd or church member might ask, which this passage answers.
Use everyday words, as real people type them. Do not name the book, the author or the chapter. One question per line, no numbering.
If the passage answers nothing (a list of titles, acknowledgements, an index, a fragment), reply NONE."""


def write_questions(passage: str) -> list[str]:
    r = llm.client().chat.completions.create(
        model=config.CLASSIFIER_MODEL, temperature=0.3, max_tokens=200,
        messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": passage}])
    lines = [" ".join(l.strip(" -*0123456789.)").split()) for l in (r.choices[0].message.content or "").splitlines()]
    return [l for l in lines if l.endswith("?")][:5]


Q_EMBEDDING_DIM = 1024   # chunks.q_embedding was built for bge-m3; the leg is parked (2026-10-14), see migration 0023


def fill_batch(conn, batch: int = BATCH, embedder=None) -> int:
    """Generate, embed and store questions for up to `batch` chunks. Returns how many were filled."""
    if config.EMBED_DIM != Q_EMBEDDING_DIM:
        raise RuntimeError(f"q_embedding is {Q_EMBEDDING_DIM}-dim; the configured model gives {config.EMBED_DIM}. "
                           "Re-create the column for the new model before generating questions.")
    with conn.transaction():
        rows = conn.execute(
            "select id, raw_content from chunks where questions is null order by source_id, id limit %s", (batch,)).fetchall()
    if not rows:
        return 0
    with ThreadPoolExecutor(PARALLEL) as pool:
        qs = list(pool.map(write_questions, [r[1] for r in rows]))
    texts = ["\n".join(q) for q in qs]
    have = [i for i, t in enumerate(texts) if t]
    vecs = dict(zip(have, (embedder or get_embedder()).embed([texts[i] for i in have]))) if have else {}
    register_vector(conn)
    with conn.transaction(), conn.cursor() as cur:
        cur.executemany("update chunks set questions = %s, q_embedding = %s where id = %s",
                        [(texts[i], vecs.get(i), rows[i][0]) for i in range(len(rows))])
    return len(rows)


def _main(argv: list[str]) -> int:
    from .db import connect
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
    done = 0
    with connect() as conn:
        left = conn.execute("select count(*) from chunks where questions is null").fetchone()[0]
        conn.commit()
        log.info("%d chunks need questions", left)
        while limit is None or done < limit:
            n = fill_batch(conn, BATCH if limit is None else min(BATCH, limit - done))
            if not n:
                break
            done += n
            log.info("filled %d / %d", done, left)
    return 0


if __name__ == "__main__":
    code = _main(sys.argv[1:])
    sys.stdout.flush()
    os._exit(code)  # torch teardown hang on macOS, see worker/main.py
