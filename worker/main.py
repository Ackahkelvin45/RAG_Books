"""Ingestion worker loop. `python -m worker.main [--once]`."""
from __future__ import annotations

import logging
import os
import sys
import time
import traceback

from shepherd import config
from shepherd.db import connect
from shepherd.questions import fill_batch

from .ingest import mark_failed, process_source

log = logging.getLogger("worker")

STALE_AFTER = "30 minutes"   # a source 'processing' longer than this is requeued
IDLE_SLEEP = 3               # seconds between polls when the queue is empty


def claim(conn):
    with conn.transaction():
        row = conn.execute("select claim_pending_source()").fetchone()
    return row


def requeue_stale(conn) -> int:
    with conn.transaction():
        ids = conn.execute("select requeue_stale_sources(%s::interval)", (STALE_AFTER,)).fetchall()
        conn.execute("delete from query_logs where expires_at < now()")  # retention, handoff section 3
        conn.execute("delete from login_failures where at < now() - interval '1 day'")
    for (sid,) in ids:
        log.warning("requeued stale source=%s", sid)
    return len(ids)


def run_one(conn) -> bool:
    row = claim(conn)
    if row is None or row[0] is None:
        return False
    (source_id,) = row
    log.info("processing source=%s", source_id)
    try:
        n = process_source(conn, source_id)
        log.info("ready source=%s chunks=%d", source_id, n)
    except Exception as e:  # noqa: BLE001 - any failure must land in failure_reason
        reason = f"{type(e).__name__}: {e}"
        log.error("failed source=%s %s\n%s", source_id, reason, traceback.format_exc())
        mark_failed(conn, source_id, reason)
    return True


def fill_questions(conn) -> int:
    """Idle work: questions for chunks that have none (new books). 0 when there is nothing to do or no API key."""
    # ponytail: no row locking; two workers idle at once may write the same chunk's questions twice (wasted calls only)
    if not config.LLM_API_KEY:
        return 0
    try:
        return fill_batch(conn)
    except Exception as e:  # noqa: BLE001 - DeepSeek down must not stop ingestion
        log.error("question fill failed: %s: %s", type(e).__name__, e)
        return 0


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    once = "--once" in argv
    drain = "--until-empty" in argv      # process the whole queue, then exit (bulk loads)
    conn = connect()
    try:
        requeue_stale(conn)
        while True:
            did = run_one(conn)
            if once or (drain and not did):
                return 0
            if not did:
                if fill_questions(conn):
                    continue
                time.sleep(IDLE_SLEEP)
                requeue_stale(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    code = main(sys.argv[1:])
    # torch on macOS can hang in interpreter teardown after the model has been
    # used. All DB work is committed and the connection closed by now, so a
    # hard exit loses nothing.
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
