"""Fill the configured embedding column for every chunk that is missing it.

    SHEPHERD_EMBED_MODEL=BAAI/bge-small-en-v1.5 SHEPHERD_EMBED_DIM=384 \
    SHEPHERD_EMBED_COLUMN=embedding_small uv run python -m worker.reembed

Resumable: it only touches rows where the column is null, so a stopped run picks up where it
left off. The other embedding column is left alone, so switching back is one env change.
"""
from __future__ import annotations

import logging
import os
import sys
import time

from pgvector.psycopg import register_vector

from shepherd import config
from shepherd.db import connect
from shepherd.embed import get_embedder

BATCH = 64
log = logging.getLogger("reembed")


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    col = config.EMBED_COLUMN
    embedder = get_embedder()
    conn = connect()
    # autocommit BEFORE the first statement: otherwise the opening select holds an implicit
    # transaction, every batch's commit is only a savepoint inside it, and the hard exit at
    # the end throws the whole run away (silently - the loop just re-reads the same rows).
    conn.autocommit = True
    register_vector(conn)
    todo = conn.execute(f"select count(*) from chunks where {col} is null").fetchone()[0]
    done = conn.execute(f"select count(*) from chunks where {col} is not null").fetchone()[0]
    log.info("%s: %d chunks to embed with %s (%d already done)", col, todo, config.EMBED_MODEL, done)
    if not todo:
        return 0
    started, processed, remaining = time.time(), 0, todo
    while remaining:
        rows = conn.execute(
            f"select id, content from chunks where {col} is null order by id limit %s", (BATCH,)).fetchall()
        if not rows:
            break
        vectors = embedder.embed([r[1] for r in rows])
        with conn.transaction(), conn.cursor() as cur:
            cur.executemany(f"update chunks set {col} = %s where id = %s",
                            [(v, r[0]) for v, r in zip(vectors, rows)])
        processed += len(rows)
        remaining -= len(rows)
        per = (time.time() - started) / processed
        log.info("%d/%d  (~%.0fs left)", processed, todo, per * remaining)
    log.info("done in %.0fs", time.time() - started)
    conn.close()
    return 0


if __name__ == "__main__":
    code = main(sys.argv[1:])
    sys.stdout.flush()
    os._exit(code)   # torch teardown hang on macOS, see worker/main.py
