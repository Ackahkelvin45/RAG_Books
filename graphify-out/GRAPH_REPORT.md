# Graph Report - RAG_sheperd  (2026-09-20)

## Corpus Check
- 93 files · ~42,715 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 796 nodes · 1548 edges · 39 communities (31 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c96314e8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- epub.py
- chunking.py
- Chat.tsx
- test_answer.py
- os
- api/main.py
- db.py
- answer.py
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- test_ingest.py
- scripture.py
- Shepherd Guide: Phase One Implementation Handoff (v3, books-only)
- compilerOptions
- compilerOptions
- connect
- Shepherd Guide
- ingest.py
- .oxlintrc.json
- React + TypeScript + Vite
- tsconfig.json
- CLAUDE.md
- 01_app_role.sh
- chat.py
- shepherd-guide
- test_retrieve.py
- test_member_never_sees_leader_chunks_on_any_path
- storage.py
- retrieve.py
- worker/main.py
- test_process_source_leaves_nothing_on_failure
- test_rls.py
- emails.py
- entrypoint.sh
- rerank.py
- test_questions.py

## God Nodes (most connected - your core abstractions)
1. `transaction()` - 37 edges
2. `fake_llm()` - 27 edges
3. `connect()` - 21 edges
4. `retrieve()` - 20 edges
5. `signup()` - 20 edges
6. `P()` - 19 edges
7. `compilerOptions` - 18 edges
8. `compilerOptions` - 15 edges
9. `process_source()` - 15 edges
10. `Shepherd Guide: Phase One Implementation Handoff (v3, books-only)` - 15 edges

## Surprising Connections (you probably didn't know these)
- `M1 — Schema, local infra` --references--> `connect()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `M1 — Schema, local infra` --references--> `transaction()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `add_chunk()` --calls--> `extract_verse_ids()`  [INFERRED]
  tests/test_retrieve.py → shared/shepherd/scripture.py
- `lifespan()` --calls--> `get_embedder()`  [INFERRED]
  api/main.py → shared/shepherd/embed.py
- `test_ministry_role_reaches_the_prompt()` --calls--> `_user()`  [INFERRED]
  tests/test_chat_api.py → shared/shepherd/answer.py

## Import Cycles
- None detected.

## Communities (39 total, 8 thin omitted)

### Community 0 - "epub.py"
Cohesion: 0.16
Nodes (16): BeautifulSoup, bs4, ebooklib, EpubBook, test_front_matter_is_skipped_and_chapters_come_from_text(), warnings, _chapter_of(), _clean() (+8 more)

### Community 1 - "chunking.py"
Cohesion: 0.27
Nodes (12): Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens(), test_overlap_repeats_tail_of_previous_chunk() (+4 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (50): react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError, ask() (+42 more)

### Community 3 - "test_answer.py"
Cohesion: 0.06
Nodes (57): datetime, ask_item(), cited_sentences(), eval_user(), generate(), injection(), judge(), load_items() (+49 more)

### Community 4 - "os"
Cohesion: 0.14
Nodes (13): functools, os, Pinned models and environment-derived settings. One place to change them., BgeM3Embedder, get_embedder(), Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a…, Shared code for the Shepherd Guide API, worker, and eval harness., fill_batch() (+5 more)

### Community 5 - "api/main.py"
Cohesion: 0.12
Nodes (33): activity(), add_user(), admin(), books(), delete_book(), delete_user(), flash(), login() (+25 more)

### Community 6 - "db.py"
Cohesion: 0.06
Nodes (29): contextlib, applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, fastapi_testclient, io (+21 more)

### Community 7 - "answer.py"
Cohesion: 0.07
Nodes (38): concurrent_futures, dataclasses, httpx, json, logging, OpenAI, ask(), attribution() (+30 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.10
Nodes (33): client(), code_for(), email(), google(), fixture, parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup() (+25 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (33): epubjs, oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript (+25 more)

### Community 11 - "test_ingest.py"
Cohesion: 0.26
Nodes (18): add_source(), make_epub(), Path, Phase 2 acceptance: EPUB -> ready, failure -> failed + reason, reingest…, status_and_chunks(), test_corrupt_file_is_marked_failed_with_reason(), test_epub_reaches_ready_with_locations_and_scripture(), test_no_pending_work_returns_false() (+10 more)

### Community 12 - "scripture.py"
Cohesion: 0.15
Nodes (19): pythonbible, book_range(), chapter_range(), extract_verse_ids(), Scripture reference extraction and formatting, via pythonbible. Verse ids are…, All verse ids referenced in `text`, sorted and de-duplicated., pythonbible raises on some prose ("...too big (pre-eminence) to receive from…, Inclusive integer range covering every verse of one chapter. (+11 more)

### Community 13 - "Shepherd Guide: Phase One Implementation Handoff (v3, books-only)"
Cohesion: 0.09
Nodes (21): 10. Observability, backups, ops, 11. Tech stack summary, 12. Open decisions (founder calls), 13. Build order, 14. Definition of done (phase 1), 1. Product framing, 2. Architecture, 3. Data model (+13 more)

### Community 14 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 15 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 16 - "connect"
Cohesion: 0.18
Nodes (16): events(), db(), db(), argparse, connect(), Open a connection as the restricted application role., cmd_add(), cmd_add_dir() (+8 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.10
Nodes (18): 1. First deployment, 2. Moving the library from the development machine, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide, Admin portal (api/) (+10 more)

### Community 18 - "ingest.py"
Cohesion: 0.12
Nodes (20): Exception, hashlib, Embedder, Protocol, context_header(), enrich(), Contextual header prepended to each chunk before embedding (handoff 4d)., build_chunks() (+12 more)

### Community 19 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 24 - "chat.py"
Cohesion: 0.05
Nodes (68): Ask, ask_endpoint(), auth_config(), book_file(), check_password(), Citation, Code, conversation() (+60 more)

### Community 28 - "test_retrieve.py"
Cohesion: 0.13
Nodes (23): _join(), merge_neighbours(), Connection, Concatenate adjacent chunks, dropping the overlap the chunker carried from…, Walk results best-first; a chunk next to one already taken (same book, same…, retrieve(), rrf(), _named() (+15 more)

### Community 29 - "test_member_never_sees_leader_chunks_on_any_path"
Cohesion: 0.21
Nodes (15): keyword_candidates(), question_candidates(), Fallback when the query is essentially just a reference and has no other words…, Chunks whose generated questions are closest in meaning to the user's question., gather(), scripture_candidates(), vector_candidates(), _where() (+7 more)

### Community 30 - "storage.py"
Cohesion: 0.23
Nodes (13): boto3, botocore_exceptions, pathlib, bucket(), _client(), delete(), download(), ensure_bucket() (+5 more)

### Community 31 - "retrieve.py"
Cohesion: 0.19
Nodes (13): collections, _main(), named_books(), names_title(), Hybrid retrieval: vector + keyword + generated-questions vector (+ scripture…, Word lists a title may be written as: the whole title, and each part around ':'…, Ids of the visible books the query names by title., SQL fragment restricting sources by the caller's role. Fails closed for unknown… (+5 more)

### Community 32 - "worker/main.py"
Cohesion: 0.20
Nodes (11): test_stale_processing_source_is_requeued(), time, traceback, mark_failed(), Connection, claim(), fill_questions(), main() (+3 more)

### Community 33 - "test_process_source_leaves_nothing_on_failure"
Cohesion: 0.29
Nodes (4): FakeEmbedder, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for…, A failure mid-ingest rolls back: no chunks, status still recoverable., test_process_source_leaves_nothing_on_failure()

### Community 35 - "emails.py"
Cohesion: 0.43
Nodes (6): html, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 40 - "rerank.py"
Cohesion: 0.18
Nodes (9): lifespan(), re, BgeReranker, FakeReranker, get_reranker(), Protocol, Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-…, Fraction of query words present in the passage. Deterministic, no model. (+1 more)

### Community 41 - "test_questions.py"
Cohesion: 0.16
Nodes (11): pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable(), test_question_list_respects_visibility(), corpus() (+3 more)

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 316 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `connect`, `chat.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `worker/main.py`, `test_answer.py`, `os`, `api/main.py`, `db.py`, `answer.py`, `Shepherd Guide: Build Guide in Phases`, `ingest.py`, `retrieve.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06956521739130435 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06009615384615385 - nodes in this community are weakly interconnected._
- **Should `os` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._
- **Should `api/main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11932773109243698 - nodes in this community are weakly interconnected._