#!/bin/sh
# api:    apply migrations, then serve the API and the web app on :8010
# worker: process queued books, backfill missing embeddings when idle
# any other args run as a command inside the image (e.g. `python -m eval.run retrieval`)
set -e
case "$1" in
  api)
    python db/migrate.py
    exec uvicorn api.main:app --host 0.0.0.0 --port 8010 --proxy-headers --forwarded-allow-ips='*'
    ;;
  worker)
    exec python -m worker.main
    ;;
  *)
    exec "$@"
    ;;
esac
