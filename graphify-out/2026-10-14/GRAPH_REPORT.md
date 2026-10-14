# Graph Report - RAG_sheperd  (2026-10-14)

## Corpus Check
- 99 files · ~46,698 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 841 nodes · 1664 edges · 45 communities (36 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a883982e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ingest.py
- chunk_text
- Chat.tsx
- test_answer.py
- embed.py
- api/main.py
- test_portal.py
- login
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- google_callback
- scripture.py
- Shepherd Guide: Phase One Implementation Handoff (v3, books-only)
- compilerOptions
- compilerOptions
- storage.py
- Shepherd Guide
- answer.py
- .oxlintrc.json
- React + TypeScript + Vite
- tsconfig.json
- CLAUDE.md
- 01_app_role.sh
- chat.py
- shepherd-guide
- test_ingest.py
- Profile
- retrieve.py
- rerank.py
- fitz
- transaction
- ask_endpoint
- UUID
- shepherd/__init__.py
- entrypoint.sh
- config.py
- epub.py
- os
- app
- worker/main.py
- pytest
- emails.py
- _warm_models

## God Nodes (most connected - your core abstractions)
1. `transaction()` - 39 edges
2. `fake_llm()` - 31 edges
3. `connect()` - 23 edges
4. `P()` - 22 edges
5. `retrieve()` - 21 edges
6. `signup()` - 21 edges
7. `compilerOptions` - 18 edges
8. `run_one()` - 16 edges
9. `get_embedder()` - 15 edges
10. `extract_verse_ids()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `M1 — Schema, local infra` --references--> `connect()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `M1 — Schema, local infra` --references--> `transaction()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `add_chunk()` --calls--> `extract_verse_ids()`  [INFERRED]
  tests/test_retrieve.py → shared/shepherd/scripture.py
- `db()` --calls--> `connect()`  [EXTRACTED]
  api/chat.py → shared/shepherd/db.py
- `touch()` --calls--> `get_embedder()`  [INFERRED]
  api/main.py → shared/shepherd/embed.py

## Import Cycles
- None detected.

## Communities (45 total, 9 thin omitted)

### Community 0 - "ingest.py"
Cohesion: 0.11
Nodes (26): Exception, pathlib, pymupdf, context_header(), enrich(), Contextual header prepended to each chunk before embedding (handoff 4d)., build_chunks(), fingerprint() (+18 more)

### Community 1 - "chunk_text"
Cohesion: 0.27
Nodes (13): Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens(), test_overlap_repeats_tail_of_previous_chunk() (+5 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (50): react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError, ask() (+42 more)

### Community 3 - "test_answer.py"
Cohesion: 0.05
Nodes (66): datetime, ask_item(), cited_sentences(), eval_user(), generate(), generate_books(), injection(), judge() (+58 more)

### Community 4 - "embed.py"
Cohesion: 0.13
Nodes (11): hashlib, BgeM3Embedder, Embedder, FakeEmbedder, get_embedder(), Protocol, Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a…, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for… (+3 more)

### Community 5 - "api/main.py"
Cohesion: 0.14
Nodes (29): activity(), add_user(), admin(), books(), db(), delete_book(), delete_user(), flash() (+21 more)

### Community 6 - "test_portal.py"
Cohesion: 0.20
Nodes (10): The cookie-signing key. It used to fall back to a fixed string when unset, in…, session_secret(), fastapi_testclient, login(), Admin portal smoke tests: auth gate, upload validation, book and user lifecycle., test_activity_renders(), test_book_upload_visibility_and_delete(), test_session_secret_is_required_behind_https() (+2 more)

### Community 7 - "login"
Cohesion: 0.15
Nodes (17): check_password(), current_user(), hash_password(), login(), login_locked(), logout(), post, Request (+9 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.09
Nodes (34): client(), code_for(), email(), google(), fixture, parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup() (+26 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (33): epubjs, oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript (+25 more)

### Community 11 - "google_callback"
Cohesion: 0.15
Nodes (16): auth_config(), book_file(), conversations(), google_callback(), _google_conf(), google_start(), google_userinfo(), Me (+8 more)

### Community 12 - "scripture.py"
Cohesion: 0.14
Nodes (20): pythonbible, book_range(), chapter_range(), extract_verse_ids(), Scripture reference extraction and formatting, via pythonbible. Verse ids are…, All verse ids referenced in `text`, sorted and de-duplicated., pythonbible raises on some prose ("...too big (pre-eminence) to receive from…, Inclusive integer range covering every verse of one chapter. (+12 more)

### Community 13 - "Shepherd Guide: Phase One Implementation Handoff (v3, books-only)"
Cohesion: 0.09
Nodes (21): 10. Observability, backups, ops, 11. Tech stack summary, 12. Open decisions (founder calls), 13. Build order, 14. Definition of done (phase 1), 1. Product framing, 2. Architecture, 3. Data model (+13 more)

### Community 14 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 15 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 16 - "storage.py"
Cohesion: 0.26
Nodes (12): boto3, botocore_exceptions, bucket(), _client(), delete(), download(), ensure_bucket(), open_book() (+4 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.10
Nodes (19): 1. First deployment, 2. Moving the library from the development machine, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide, Using your own nginx instead of Caddy (+11 more)

### Community 18 - "answer.py"
Cohesion: 0.12
Nodes (24): ask(), attribution(), _citation(), _format_passages(), generate(), _history(), _main(), Grounded chat for shepherds and pastors (contract: handoff section 6, books… (+16 more)

### Community 19 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 24 - "chat.py"
Cohesion: 0.12
Nodes (23): Citation, Code, ConversationSummary, db(), Location, MessageOut, OK, _otp_hash() (+15 more)

### Community 27 - "test_ingest.py"
Cohesion: 0.21
Nodes (24): add_source(), make_epub(), make_pdf(), Path, Phase 2 acceptance: EPUB -> ready, failure -> failed + reason, reingest…, A failure mid-ingest rolls back: no chunks, status still recoverable., status_and_chunks(), test_corrupt_file_is_marked_failed_with_reason() (+16 more)

### Community 28 - "Profile"
Cohesion: 0.22
Nodes (7): Profile, Required once after sign-up. The first save also sends the welcome email., save_profile(), SignIn, date, field_validator, put

### Community 29 - "retrieve.py"
Cohesion: 0.05
Nodes (64): collections, parked, pgvector_psycopg, get_reranker(), _join(), keyword_candidates(), _main(), merge_neighbours() (+56 more)

### Community 30 - "rerank.py"
Cohesion: 0.15
Nodes (8): re, BgeReranker, FakeReranker, Protocol, Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-…, Fraction of query words present in the passage. Deterministic, no model., Reranker, typing

### Community 32 - "transaction"
Cohesion: 0.15
Nodes (23): argparse, connect(), lookup_user_by_email(), Connection, Database access helpers. The app connects as the restricted `shepherd_app`…, Open a connection as the restricted application role., Run a block in one transaction. Commits on success, rolls back on error., Pre-auth lookup: email -> user/role, via the security-definer function. (+15 more)

### Community 33 - "ask_endpoint"
Cohesion: 0.22
Nodes (9): Ask, ask_endpoint(), events(), conversation(), delete_conversation(), EventStream, _own(), Runs the full pipeline: classify → search the books → answer from the passages… (+1 more)

### Community 35 - "shepherd/__init__.py"
Cohesion: 0.14
Nodes (12): concurrent_futures, httpx, logging, Shared code for the Shepherd Guide API, worker, and eval harness., Outgoing email via Resend (https://resend.com). Without RESEND_API_KEY the…, fill_batch(), _main(), Questions each passage answers (improvement stage 4). DeepSeek writes 3-5… (+4 more)

### Community 37 - "config.py"
Cohesion: 0.17
Nodes (12): dataclasses, functools, json, OpenAI, classify(), lexicon_hit(), Scope classifier, run before retrieval. off_scope -> polite decline. sensitive…, Verdict (+4 more)

### Community 38 - "epub.py"
Cohesion: 0.18
Nodes (14): BeautifulSoup, bs4, ebooklib, EpubBook, test_front_matter_is_skipped_and_chapters_come_from_text(), warnings, _chapter_of(), _clean() (+6 more)

### Community 39 - "os"
Cohesion: 0.27
Nodes (9): contextlib, applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, io, os (+1 more)

### Community 40 - "app"
Cohesion: 0.18
Nodes (11): admin(), app(), isolate_sources(), fixture, Superuser connection. Used only to set up and tear down fixtures., Restricted application role., Every source (and its chunks, via cascade) created during a test is removed…, One throwaway source with one chunk. (+3 more)

### Community 41 - "worker/main.py"
Cohesion: 0.22
Nodes (8): traceback, mark_failed(), Connection, claim(), fill_embeddings(), main(), Ingestion worker loop. `python -m worker.main [--once]`., Idle work: embed chunks whose configured column is empty (after a model switch,…

### Community 43 - "emails.py"
Cohesion: 0.43
Nodes (6): html, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 44 - "_warm_models"
Cohesion: 0.70
Nodes (5): Load the embedding and reranking models at startup (~45 s), not on the first…, _warm_models(), keep_warm(), lifespan(), touch()

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 332 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `transaction`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `transaction()` connect `transaction` to `ingest.py`, `ask_endpoint`, `api/main.py`, `login`, `Shepherd Guide: Build Guide in Phases`, `worker/main.py`, `google_callback`, `chat.py`, `test_ingest.py`, `Profile`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1103448275862069 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06956521739130435 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.053313587560162905 - nodes in this community are weakly interconnected._
- **Should `embed.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._