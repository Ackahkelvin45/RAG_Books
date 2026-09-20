# Shepherd Guide — Phase 1 Implementation Plan (books only)

Derived from `shepherd-guide-phase1-handoff.md` (v3). Copyright posture is settled and is
out of scope for this plan. Audio stays deferred. This plan turns the handoff into an ordered
set of milestones, each with concrete deliverables and an acceptance check, so the build can
proceed milestone by milestone with a working system at every step.

Toolchain on this machine: Python 3.13, Node 22, Docker. No local psql; Postgres runs in Docker.

---

## 0. Decisions made in this plan (assumptions, changeable)

| Area | Choice | Reason |
|---|---|---|
| Repo layout | Single repo: `db/`, `api/`, `worker/`, `shared/` (Python), `web/` (Next.js), `eval/`, `infra/` | One deploy unit in phase 1; shared Python code for retrieval/scripture/embedding |
| Python packaging | `uv` workspace, one `pyproject.toml` per service plus `shared/` | Fast, lockfile, works on CPU-only VM |
| Local infra | `docker compose`: `pgvector/pgvector:pg16`, MinIO (S3-compatible) | Matches prod shape; no cloud needed to develop |
| Migrations | Numbered SQL files in `db/migrations/`, applied by a small `db/migrate.py` | Schema is the spec; SQL is clearer to read than through an ORM |
| DB access | `psycopg` 3 + raw SQL, no ORM | Vector/tsvector SQL is clearer without an ORM |
| Job queue | `sources.status = 'pending'` claimed with `FOR UPDATE SKIP LOCKED` | Postgres-backed queue as specified; no extra service |
| Embeddings | `BAAI/bge-m3` dense via `sentence-transformers`, 1024-dim, normalized | Pinned per handoff |
| Reranker | `BAAI/bge-reranker-v2-m3` via `sentence-transformers` CrossEncoder | Pinned per handoff; CPU is fine for 20 candidates |
| Generation model | DeepSeek `deepseek-chat` via its OpenAI-compatible API (`openai` SDK, `base_url=https://api.deepseek.com`), streamed, low temperature | Founder decision 2026-09-18. The handoff's refusal-quality concern about non-Claude models is real: the phase 6 refusal/redirect/injection gates decide whether it holds |
| Scope classifier | `deepseek-chat` with JSON output mode, plus a Twi keyword pre-filter | Multilingual gate is a release gate; per-language redirect accuracy is measured in phase 6 |
| Eval judge | `deepseek-chat`, pinned, 3 runs per item, gate on the mean | Per handoff section 9 |
| Users | Members, shepherds and pastors (founder decisions 2026-09-19). Advisor voice, but every point drawn from the books and cited; the app appends the book/chapter attribution from real citations. Per-user persistent conversations. Books default to visible to all; admins can mark one leader-only. | Grounded pastoral chatbot |
| Deployment | Single church, no multi-tenancy. Corpus is the books of Dag Heward-Mills, owned by First Love Church. | Founder decision, 2026-09-14, supersedes the handoff's multi-tenant requirement |

---

## 1. Repository layout

```
RAG_sheperd/
  docker-compose.yml          postgres+pgvector, minio, api, worker, web
  .env.example
  db/
    migrations/0001_init.sql  extension, tables, indexes
    migrations/0002_seed.sql  first admin user
    migrate.py
  shared/                     python package `shepherd`
    shepherd/db.py            connection, transaction helpers
    shepherd/embed.py         bge-m3 loader + embed_texts()
    shepherd/rerank.py        bge-reranker loader + rerank()
    shepherd/scripture.py     pythonbible wrappers: extract ids, format, range from ref
    shepherd/chunking.py      recursive chunker, chapter-bounded, overlap
    shepherd/enrich.py        context header template
    shepherd/storage.py       S3 get/put keyed by source id
  worker/
    worker/main.py            claim loop
    worker/parsers/epub.py
    worker/parsers/pdf_text.py
    worker/parsers/pdf_ocr.py
    worker/ingest.py          parse -> chunk -> enrich -> scripture -> embed -> store; supersede tx
  api/
    api/main.py               FastAPI app
    api/auth.py
    api/classify.py           scope classifier
    api/retrieve.py           hybrid retrieval (vector + FTS + scripture) -> RRF -> rerank
    api/generate.py           contract prompt, streaming, citation assembly
    api/routes/query.py       POST /query (SSE stream)
    api/routes/sources.py     upload, list, status, reingest
    api/routes/eval.py        run eval, report
    api/prompts/              versioned prompt files (contract_v1.md, classifier_v1.md)
  eval/
    items/                    seed eval items as YAML/JSON, imported to eval_items
    run.py                    one-command harness -> report + exit code
    judges.py                 per-citation entailment, refusal/redirect/injection checks
  web/                        Next.js (last milestone)
  tests/                      pytest: visibility leak, scripture ranges, parsers
```

---

## 2. Milestones

Each milestone ends with a runnable state and a check. Do not start the next until the check passes.

### M1 — Schema, local infra
Deliverables
- `docker-compose.yml` with pgvector Postgres and MinIO; `.env.example`.
- `0001_init.sql`: schema (users, sources, chunks, query_logs, eval_items), indexes, `updated_at` trigger on `sources`.
- `0002_seed.sql`: one admin user.
- `shared/shepherd/db.py`: `connect()`, `transaction()` helper.
- App DB role that is **not** table owner, so privileges are explicit.
- `tests/test_rls.py` (renamed `test_schema.py`): FK cascade and auth lookup.

Check: `uv run pytest tests/test_rls.py` passes against the compose Postgres.

### M2 — Ingestion worker, EPUB first
Deliverables
- `worker/main.py`: loop claiming one `pending` source with `FOR UPDATE SKIP LOCKED`, setting `processing`, dispatching on file extension, writing `ready` or `failed` + `failure_reason`. Any exception is caught at the top; nothing is left `processing`.
- `parsers/epub.py`: `ebooklib`, walk spine, strip HTML, yield `(chapter_index, chapter_title, text)`.
- `chunking.py`: recursive split, 300–500 tokens (bge-m3 tokenizer for counting), ~15% overlap, never crosses a chapter boundary.
- `enrich.py`: header `"From {title} by {author}{, series}. Chapter {n}: {chapter_title}."` prepended to `content`; `raw_content` untouched.
- `scripture.py`: `pythonbible.get_references()` → verse ids; also `range_for_chapter(book, chapter)` and `range_for_book(book)`.
- `embed.py`: bge-m3 loaded once per process, batch encode, normalized.
- `ingest.py`: writes chunks in one transaction; `location = {"chapter": n, "title": ...}`.
- Re-ingestion: `POST /sources/{id}/reingest` creates a new `sources` row with `version + 1`; the worker, after inserting the new chunks, in one transaction marks the old row `superseded`, sets `superseded_by`, and deletes its chunks.
- Storage: files under `s3://{bucket}/{source_id}/{filename}`.

Check: one public-domain EPUB reaches `ready` with chunks that have chapter locations and non-empty `scripture` where the text cites verses. A deliberately corrupted file reaches `failed` with a readable `failure_reason`. Re-ingest leaves exactly one `ready` row and no orphan chunks.

### M3 — PDF branches
Deliverables
- `parsers/pdf_text.py`: PyMuPDF; per-page text; chapter derived from the PDF outline when present, else `chapter: null`. `location = {"page": n, "chapter": c}`.
- Text-layer detection: mean chars per page below a configurable threshold (default 50) routes to OCR.
- `parsers/pdf_ocr.py`: rasterize at 300 dpi, Tesseract via `pytesseract`; per-page confidence recorded; source `meta.needs_review = true` and `meta.ocr_mean_conf` stored. Vision-model fallback is a stub behind a flag in phase 1, not built.
- Scanned chunking: chunk per page, then merge short adjacent pages up to the token target, still chapter-bounded when an outline exists.

Check: one born-digital PDF and one scanned PDF both reach `ready`; the scanned one is flagged for review; page citations resolve to the correct page when opened.

### M4 — Hybrid retrieval and rerank
Deliverables
- `api/retrieve.py`:
  1. Vector: `embedding <=> $q` cosine, top 30.
  2. Keyword: `ts_doc @@ websearch_to_tsquery('english', $q)`, ranked by `ts_rank_cd`, top 30.
  3. Scripture: run pythonbible on the query; if it yields refs, add `scripture && $ids` as a pre-filter to both queries; for a chapter-only ref ("Romans 8") use the integer range.
  4. RRF with k=60.
  5. Rerank fused top 20 with bge-reranker-v2-m3; keep top 8 above a score floor.
- Visibility filter lives in the SQL of both queries: `join sources s ... and (:role = 'leader' or s.visibility = 'member') and s.status = 'ready'`.
- `tests/test_visibility.py`: a leader-only source and a member source; a member-role retrieval never returns a leader-only chunk, across vector, keyword, and scripture paths.
- `tests/test_scripture.py`: query "John 3:16" returns chunks whose `scripture` contains 43003016; "Romans 8" returns chunks in range 45008001–45008999 and none from Romans 7 or 9.

Check: both test files pass; a manual query against the ingested books returns sensible reranked passages with correct chapter/page.

### M5 — Scope classifier and generation contract
Deliverables
- `api/prompts/classifier_v1.md` and `api/classify.py`: Sonnet 5, structured output `{label: answerable|sensitive|off_scope, category, language: en|tw|mixed, confidence}`. A Twi lexicon pre-filter (`shared/shepherd/twi_lexicon.py`, seeded from a native reviewer, machine translation only as a starting draft flagged for review) forces `sensitive` on a hit regardless of model output. Fail closed: any API error or refusal on the classifier call yields `sensitive` → redirect.
- Redirect response: fixed template naming a shepherd and contact channel from config; no retrieval.
- `api/prompts/contract_v1.md`: the section-6 contract verbatim, plus passage delimiters (`<passage id="…" book="…" chapter="…" page="…">…</passage>`) and the instruction that passage contents are data and never instructions.
- `api/generate.py`: Opus 5, `client.messages.stream`, adaptive thinking, effort `low`, `fallbacks: "default"`, `max_tokens` ~4000. Passages are sent as `raw_content` (users must see verbatim text). Model cites by passage id; the API maps ids back to `{book, author, chapter, page}` and streams `{type: "text" | "citation"}` SSE events.
- Conflict handling and thin-corpus refusal are prompt behaviors, tested in M6.
- `POST /query`: classify → (redirect | decline | retrieve → generate); every query writes a `query_logs` row with `classification` and `retrieved_ids`.
- Nightly job deleting `query_logs where expires_at < now()`.

Check: manual runs cover an answerable question, a question the corpus does not cover (clean refusal), a sensitive question in English, Twi, and code-switched form (all redirect), and a passage with an embedded instruction (ignored).

### M6 — Evaluation harness
Deliverables
- `eval/items/*.yaml` seed set of ~10, growing to 50+: ~60% answerable with `expected_source_id`, ~20% refuse, ~20% redirect split across en/tw/mixed, ≥2 injection probes. Twi items marked `needs_native_review` until signed off.
- `eval/run.py`: one command, runs every item through `POST /query` internals, produces JSON and a markdown report, exit code non-zero on a gated regression once `n >= 50` (advisory before).
- Metrics:
  - Retrieval hit rate: expected source in reranked top-k.
  - Citation faithfulness, per citation: split the answer into (claim, cited passage) pairs; Sonnet 5 judge answers `supported | not_supported` for that specific pair; 3 runs, mean.
  - Refusal accuracy, redirect accuracy per language, injection resistance.
  - RAGAS context precision/recall as a secondary signal only.
- Baseline JSON committed; CI compares against it.

Check: `uv run eval/run.py` prints all metrics and exits 0 on the seed set.

### M7 — Observability, backups, ops
Deliverables
- Sentry SDK in `api` and `worker`.
- Prometheus metrics endpoint on api and worker: ingestion failures, queue depth, query latency histogram, classifier errors, Claude API error/timeout counts. Alertmanager rules for each.
- Structured JSON logs, Promtail → Loki.
- `infra/backup.sh`: nightly `pg_dump` + WAL archiving to S3; `infra/RESTORE.md` with a drilled PITR procedure and the date it was last exercised. S3 versioning on the raw-files bucket.
- One Grafana board: queries/day by classification, redirects by language, ingestion status, estimated spend from token usage.

Check: force a worker failure and confirm an alert fires; perform one PITR restore drill and record it.

### M8 — Minimal web UI
Deliverables
- Next.js app: login, upload (drag EPUB/PDF, shows status and `failure_reason`), ask box with streamed answer, citation cards showing book, author, chapter, page, and the verbatim `raw_content`; a scripture reference in a passage renders the verse from pythonbible's public-domain text.
- Admin page: sources list, reingest button, review flag for OCR'd books.

Check: a leader can upload a book, wait for `ready`, ask a question, and click through a citation to the exact passage.

---

## 3. Cross-cutting rules

- Prompts are versioned files; the version string is logged on every query so eval results are attributable.
- Models are pinned in one config module (`shared/shepherd/config.py`): `GEN_MODEL`, `CLASSIFIER_MODEL`, `JUDGE_MODEL` all `deepseek-chat`; `LLM_BASE_URL`, `LLM_API_KEY` alongside.
- All LLM calls go through the `openai` Python SDK pointed at DeepSeek: streaming for generation, JSON mode for the classifier and judge, typed exception handling. Fail closed: a classifier error means redirect.
- `raw_content` is what users see and what the model is given; `content` (enriched) exists only for embedding and FTS.

---

## 4. Test matrix (CI)

| Test | Milestone | Gate |
|---|---|---|
| EPUB / digital PDF / scanned PDF reach `ready` | M2–M3 | hard |

---

## 5. Order of work for the first two weeks

1. M1 end to end (compose, migrations, schema test). Half a day to a day.
2. M2 with a public-domain EPUB (Project Gutenberg has many Christian classics with dense scripture citations, good for scripture tests). Two to three days.
3. M4 retrieval directly on that book, with the leak test. One to two days.
4. M5 classifier and generation. Two days.
5. M3 PDF branches. One to two days.
6. M6 harness with the ~10 seed items, then grow toward 50 with the church.
7. M7, then M8.

---

## 6. Still needed from the founder (not blocking M1–M4)

- Twi reviewer for the sensitive lexicon and eval items (blocks the M5 release gate, not the build).
- Shepherd contact details for the redirect template.
- Confirmation of the 180-day `query_logs` retention default.
- First three to five books from First Love to ingest as the real corpus.
