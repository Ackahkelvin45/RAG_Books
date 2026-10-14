"""Fill the configured embedding column for every chunk that is missing it.

    SHEPHERD_EMBED_MODEL=BAAI/bge-base-en-v1.5 SHEPHERD_EMBED_DIM=768 \
    SHEPHERD_EMBED_COLUMN=embedding_base uv run python -m worker.reembed

One transaction per batch, so a stopped run picks up where it left off. The worker calls `fill_batch`
whenever it is idle, so after a model switch (or a book ingested while another column was selected)
the library heals itself without anyone remembering to run this. The other columns are left alone.
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


def fill_batch(conn, embedder=None, batch: int = BATCH) -> int:
    """Embed up to `batch` chunks whose configured column is null. Returns how many were filled."""
    col = config.EMBED_COLUMN
    register_vector(conn)
    with conn.transaction():
        rows = conn.execute(f"select id, content from chunks where {col} is null order by id limit %s", (batch,)).fetchall()
        if not rows:
            return 0
        vectors = (embedder or get_embedder()).embed([r[1] for r in rows])
        with conn.cursor() as cur:
            cur.executemany(f"update chunks set {col} = %s where id = %s", [(v, r[0]) for v, r in zip(vectors, rows)])
    return len(rows)


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    col = config.EMBED_COLUMN
    embedder = get_embedder()
    conn = connect()
    conn.autocommit = True      # the counts below must not open a transaction that swallows every batch's commit
    todo = conn.execute(f"select count(*) from chunks where {col} is null").fetchone()[0]
    log.info("%s: %d chunks to embed with %s", col, todo, config.EMBED_MODEL)
    started, done = time.time(), 0
    while n := fill_batch(conn, embedder):
        done += n
        per = (time.time() - started) / done
        log.info("%d/%d  (~%.0fs left)", done, todo, per * (todo - done))
    log.info("done in %.0fs", time.time() - started)
    conn.close()
    return 0


if __name__ == "__main__":
    code = main(sys.argv[1:])
    sys.stdout.flush()
    os._exit(code)   # torch teardown hang on macOS, see worker/main.py
