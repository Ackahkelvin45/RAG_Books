# Shepherd Guide

Grounded, cited retrieval over a church's own books. Single-church deployment for First Love Church; the corpus is the books of Dag Heward-Mills. See
`shepherd-guide-phase1-handoff.md` (spec), `PLAN.md` (technical plan) and
`BUILD-PHASES.md` (plain-language phases).

## Deploying

See [DEPLOY.md](DEPLOY.md): one server, `docker compose -f docker-compose.prod.yml up -d --build`, HTTPS via Caddy,
nightly backups, and how to copy the processed library across from this machine.

## Local setup

```bash
cp .env.example .env          # once
docker compose up -d          # Postgres (pgvector, host port 5433) + MinIO
uv sync                       # Python deps into .venv
uv run python db/migrate.py   # apply migrations
uv run pytest                 # phase 1 acceptance tests
```

Reset the database completely: `docker compose down -v && docker compose up -d`.

MinIO console: http://localhost:9001 (user/password from `.env`).

## Ingesting a book (phase 2)

```bash
# queue a book (uploads to MinIO, creates a pending source row)
uv run python -m worker.cli add path/to/book.epub --title "Title" --author "Author"

# queue a whole folder (title from each file; skips titles already loaded)
uv run python -m worker.cli add-dir ~/Downloads/131-dagbooks-en --author "Bishop Dag Heward-Mills"

# process pending books: --once handles one, --until-empty drains the queue and exits,
# no flag polls forever. For a long load, detach it and keep the Mac awake:
#   nohup caffeinate -i uv run python -m worker.main --until-empty > logs/bulk-load.log 2>&1 &
uv run python -m worker.main --once

# see every book, its version, status, chunk count and any failure reason
uv run python -m worker.cli list

# re-process a book: creates version+1, and on success supersedes the old version
uv run python -m worker.cli reingest <source_id>
```

The first worker run downloads the bge-m3 embedding model (about 2 GB) into the
Hugging Face cache. Keep `HF_HUB_DISABLE_XET=1` in `.env`: the hub's xet transfer
protocol stalls on some networks, plain HTTP does not. Tests set
`SHEPHERD_EMBEDDER=fake` and never load the model.

A book left in `processing` for over 30 minutes (worker crash) is requeued
automatically the next time a worker starts or idles.

## Searching (phase 3)

```bash
# hybrid search: vector + keyword (+ scripture filter) -> RRF -> rerank, top 8
uv run python -m shepherd.retrieve "what does the book teach about despair"
uv run python -m shepherd.retrieve "Romans 8"                 # chapter range filter
uv run python -m shepherd.retrieve "hope" --role member       # member sees member-visibility books only
```

Visibility is enforced in the SQL of every candidate query (see
`shared/shepherd/retrieve.py`), and `tests/test_retrieve.py` proves a member
role cannot retrieve leader-only chunks on the vector, keyword, or scripture path.
The first search downloads the bge-reranker-v2-m3 model (about 2 GB).

## Asking (phase 4)

```bash
# chat for shepherds/pastors: classify -> (decline | retrieve -> grounded, cited answer with read links),
# conversation history remembered per user, persisted to conversations/messages, logged to query_logs
uv run python -m shepherd.answer "What happens at Doubting Castle?" --user admin@firstlove.example
uv run python -m shepherd.answer "and how do they escape?" --user admin@firstlove.example --conversation <id>
```

Needs `DEEPSEEK_API_KEY` in `.env`. Members, shepherds and pastors all chat with it. Advice voice, books-only content, every reply ends with the book and chapter it came from, built from the real citations.
crisis lexicon live in `shared/shepherd/classify.py` and `shared/shepherd/answer.py`.

## Scoring quality (eval/)

```bash
uv run python -m eval.run seed                 # load the hand-written questions in eval/seed.jsonl
uv run python -m eval.run generate --n 150     # DeepSeek writes a question per sampled passage (one-off, cents)
uv run python -m eval.run retrieval            # search only: is the right passage/book found? free, ~20 min on CPU
uv run python -m eval.run full                 # end to end with DeepSeek: refusals, citations, crisis, injection (~$0.50)
```

Add `--kind hand` or `--limit N` for a quicker run. Each run is saved in `eval/results/` and printed next to the
previous run of the same mode, so a change can be judged before it ships. `query_logs` also records the search
query, the reranker score of each retrieved passage, and which passages were cited.

## Admin portal (api/)

```bash
uv run uvicorn api.main:app --reload --port 8000     # then open http://localhost:8000/admin
uv run python -m worker.main                         # keep a worker running to process uploads
```

Sign in with `ADMIN_PASSWORD` from `.env`. Books: upload EPUB/PDF, watch status, re-process,
set "everyone" or "leaders only", mark scanned books reviewed, delete. Users: add members,
leaders and admins, change roles, remove. Activity: last 30 days by classification and the
latest questions. The member chat UI will live on the same app.

## API documentation (Swagger)

With the API running, open http://localhost:8010/docs for interactive Swagger docs
(http://localhost:8010/redoc for a read-only layout, /openapi.json for the raw spec).
Sign in with `POST /api/login` under **Try it out**; the session cookie then applies to every
other call on the page. Endpoint docs live next to the code in `api/chat.py`.

## Chat app (web/, React + Vite)

```bash
# development: hot reload on :5173, /api proxied to the backend on :8010
uv run uvicorn api.main:app --reload --port 8010
cd web && npm install && npm run dev            # open http://localhost:5173

# production: build once, then FastAPI serves the app and the API on one port
cd web && npm run build                         # writes web/dist
uv run uvicorn api.main:app --port 8010         # open http://localhost:8010  (admin portal: /admin)
```

Screens: sign in / create account, chat (conversation list, streamed answers, citation
chips, source cards), and a read page per passage (full passage, previous/next, and ASV
text of the verses it cites). New accounts are members; promote shepherds and pastors to
`leader` in the admin portal. JSON API lives in `api/chat.py`.

## Sign-up, Google sign-in and profiles

Email sign-ups first confirm a 6-digit code sent to their inbox (10-minute expiry, 5 tries,
60-second resend cooldown); Google sign-ups skip this. Nothing past sign-up works until the
email is confirmed. Codes are sent with Resend (`RESEND_API_KEY` and `MAIL_FROM` in `.env`); with no key set
they are printed to the API log instead, for local testing only.

After confirming (or signing in with Google), people complete a one-time profile: first and last name
(skipped when Google provided them), date of birth, and whether they are a member, shepherd or
pastor. That choice is shown to the AI and in the admin Users page; it does NOT grant access.
Access (`member` / `leader` / `admin`) is set by an admin in the portal.

Google sign-in turns on when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`:

1. Google Cloud Console → APIs & Services → OAuth consent screen: External, app name, support email.
2. Credentials → Create credentials → OAuth client ID → Web application.
3. Authorised redirect URI: `{PUBLIC_URL}/api/auth/google/callback`
   (locally `http://localhost:8010/api/auth/google/callback`).
4. Put the client ID and secret in `.env`, set `PUBLIC_URL`, restart the API.

A Google account whose email matches an existing email account is linked to it; the password keeps working.
