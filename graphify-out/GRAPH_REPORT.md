# Graph Report - RAG_sheperd  (2026-10-14)

## Corpus Check
- 100 files · ~48,363 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 855 nodes · 1697 edges · 53 communities (43 shown, 10 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.88)
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
- run.py
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- retrieve.py
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
- test_retrieve.py
- test_questions.py
- rerank.py
- fitz
- connect
- process_source
- UUID
- logging
- entrypoint.sh
- shepherd/__init__.py
- epub.py
- conftest.py
- app
- worker/main.py
- pytest
- os
- db.py
- named_books
- merge_neighbours
- test_member_never_sees_leader_chunks_on_any_path
- classify.py
- FakeLLM
- test_ask_streams_and_persists
- client
- test_passage_respects_visibility_and_links_neighbours

## God Nodes (most connected - your core abstractions)
1. `transaction()` - 39 edges
2. `fake_llm()` - 33 edges
3. `P()` - 24 edges
4. `connect()` - 23 edges
5. `retrieve()` - 22 edges
6. `signup()` - 22 edges
7. `compilerOptions` - 18 edges
8. `run_one()` - 18 edges
9. `get_embedder()` - 15 edges
10. `extract_verse_ids()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `M1 — Schema, local infra` --references--> `connect()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `M1 — Schema, local infra` --references--> `transaction()`  [INFERRED]
  PLAN.md → shared/shepherd/db.py
- `add_chunk()` --calls--> `extract_verse_ids()`  [INFERRED]
  tests/test_retrieve.py → shared/shepherd/scripture.py
- `touch()` --calls--> `get_embedder()`  [INFERRED]
  api/main.py → shared/shepherd/embed.py
- `touch()` --calls--> `get_reranker()`  [INFERRED]
  api/main.py → shared/shepherd/rerank.py

## Import Cycles
- None detected.

## Communities (53 total, 10 thin omitted)

### Community 0 - "ingest.py"
Cohesion: 0.14
Nodes (19): Exception, pathlib, pymupdf, context_header(), enrich(), Contextual header prepended to each chunk before embedding (handoff 4d)., build_chunks(), parse_file() (+11 more)

### Community 1 - "chunk_text"
Cohesion: 0.27
Nodes (13): Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens(), test_overlap_repeats_tail_of_previous_chunk() (+5 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (50): react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError, ask() (+42 more)

### Community 3 - "test_answer.py"
Cohesion: 0.12
Nodes (32): fake_llm(), P(), pastor(), fixture, parametrize, Phase 4: classifier, contract behaviours, conversation memory, logging. No…, test_a_second_search_waits_for_the_first(), run() (+24 more)

### Community 4 - "embed.py"
Cohesion: 0.11
Nodes (14): hashlib, BgeM3Embedder, Embedder, FakeEmbedder, get_embedder(), Protocol, Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a…, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for… (+6 more)

### Community 5 - "api/main.py"
Cohesion: 0.11
Nodes (37): activity(), add_user(), admin(), books(), db(), delete_book(), delete_user(), flash() (+29 more)

### Community 6 - "test_portal.py"
Cohesion: 0.20
Nodes (10): The cookie-signing key. It used to fall back to a fixed string when unset, in…, session_secret(), fastapi_testclient, login(), Admin portal smoke tests: auth gate, upload validation, book and user lifecycle., test_activity_renders_and_hides_sensitive_text(), test_book_upload_visibility_and_delete(), test_session_secret_is_required_behind_https() (+2 more)

### Community 7 - "run.py"
Cohesion: 0.10
Nodes (36): datetime, ask_item(), cited_sentences(), eval_user(), generate(), generate_books(), injection(), judge() (+28 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.12
Nodes (26): code_for(), email(), parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup(), start_google(), test_book_file_streams_epub_with_visibility_and_download_name(), test_code_format_is_validated() (+18 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (33): epubjs, oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript (+25 more)

### Community 11 - "retrieve.py"
Cohesion: 0.18
Nodes (15): collections, _main(), question_candidates(), Hybrid retrieval: vector + keyword + generated-questions vector (+ scripture…, Chunks whose generated questions are closest in meaning to the user's question., Fallback when the query is essentially just a reference and has no other words…, SQL fragment restricting sources by the caller's role. Fails closed for unknown…, gather() (+7 more)

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
Cohesion: 0.09
Nodes (20): 1. First deployment, 2. Moving the library from the development machine, 2b. Replacing the library on a server that already has one, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide (+12 more)

### Community 18 - "answer.py"
Cohesion: 0.12
Nodes (25): ask(), attribution(), _citation(), _format_passages(), generate(), _history(), _plain(), Grounded chat for shepherds and pastors (contract: handoff section 6, books… (+17 more)

### Community 19 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 24 - "chat.py"
Cohesion: 0.05
Nodes (68): Ask, ask_endpoint(), auth_config(), book_file(), check_password(), Citation, Code, conversation() (+60 more)

### Community 27 - "test_ingest.py"
Cohesion: 0.21
Nodes (22): add_source(), make_epub(), make_pdf(), Path, Phase 2 acceptance: EPUB -> ready, failure -> failed + reason, reingest…, A failure mid-ingest rolls back: no chunks, status still recoverable., status_and_chunks(), test_corrupt_file_is_marked_failed_with_reason() (+14 more)

### Community 28 - "test_retrieve.py"
Cohesion: 0.22
Nodes (13): Connection, `timings`, when given, receives embed_ms, sql_ms and rerank_ms for query_logs., retrieve(), rrf(), Phase 3 acceptance: visibility leak test, scripture filtering, fusion, keyword…, test_final_k_is_respected(), test_hard_scripture_filter_keeps_only_citing_passages(), test_named_book_restricts_search() (+5 more)

### Community 29 - "test_questions.py"
Cohesion: 0.15
Nodes (12): parked, pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable(), test_question_list_respects_visibility() (+4 more)

### Community 30 - "rerank.py"
Cohesion: 0.19
Nodes (8): re, BgeReranker, FakeReranker, get_reranker(), Protocol, Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-…, Fraction of query words present in the passage. Deterministic, no model., Reranker

### Community 32 - "connect"
Cohesion: 0.20
Nodes (16): events(), db(), argparse, connect(), Open a connection as the restricted application role., cmd_add(), cmd_add_dir(), cmd_list() (+8 more)

### Community 33 - "process_source"
Cohesion: 0.18
Nodes (11): enqueue_reingest(), fingerprint(), process_source(), Connection, Create a new pending version of a source. Returns the new source id., Same text + same embedding model => the old embedding (and questions) can be…, Progress the admin page can see while the ingest transaction is open (own…, fingerprint -> (embedding, questions, q_embedding) from the version being… (+3 more)

### Community 35 - "logging"
Cohesion: 0.40
Nodes (3): httpx, logging, Outgoing email via Resend (https://resend.com). Without RESEND_API_KEY the…

### Community 37 - "shepherd/__init__.py"
Cohesion: 0.16
Nodes (12): concurrent_futures, functools, OpenAI, Pinned models and environment-derived settings. One place to change them., Shared code for the Shepherd Guide API, worker, and eval harness., client(), One OpenAI-compatible client pointed at DeepSeek. Tests swap `client()` via…, fill_batch() (+4 more)

### Community 38 - "epub.py"
Cohesion: 0.17
Nodes (15): BeautifulSoup, bs4, ebooklib, EpubBook, test_front_matter_is_skipped_and_chapters_come_from_text(), test_parse_epub_yields_chapters(), warnings, _chapter_of() (+7 more)

### Community 39 - "conftest.py"
Cohesion: 0.33
Nodes (7): applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, io, psycopg

### Community 40 - "app"
Cohesion: 0.18
Nodes (11): admin(), app(), isolate_sources(), fixture, Superuser connection. Used only to set up and tear down fixtures., Restricted application role., Every source (and its chunks, via cascade) created during a test is removed…, One throwaway source with one chunk. (+3 more)

### Community 41 - "worker/main.py"
Cohesion: 0.22
Nodes (11): test_no_pending_work_returns_false(), traceback, mark_failed(), alert_failure(), claim(), fill_embeddings(), main(), Ingestion worker loop. `python -m worker.main [--once]`. (+3 more)

### Community 43 - "os"
Cohesion: 0.36
Nodes (7): html, os, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 44 - "db.py"
Cohesion: 0.22
Nodes (7): contextlib, _main(), lookup_user_by_email(), Connection, Database access helpers. The app connects as the restricted `shepherd_app`…, Pre-auth lookup: email -> user/role, via the security-definer function., typing

### Community 45 - "named_books"
Cohesion: 0.28
Nodes (9): named_books(), names_title(), Word lists a title may be written as: the whole title, and each part around ':'…, Ids of the visible books the query names by title., title_forms(), _named(), parametrize, test_a_named_book_is_recognised() (+1 more)

### Community 46 - "merge_neighbours"
Cohesion: 0.29
Nodes (8): _join(), merge_neighbours(), Concatenate adjacent chunks, dropping the overlap the chunker carried from…, Walk results best-first; a chunk next to one already taken (same book, same…, _p(), test_join_drops_the_carried_overlap(), test_merge_respects_chapter_and_cap(), test_neighbours_merge_in_reading_order_and_free_a_slot()

### Community 47 - "test_member_never_sees_leader_chunks_on_any_path"
Cohesion: 0.36
Nodes (8): keyword_candidates(), ids_of(), A natural question with words absent from the passage must still match on the…, The leak test. Every candidate path is checked independently, then the full…, test_keyword_path_does_not_require_every_word(), test_keyword_path_finds_exact_words(), test_keyword_ranking_rewards_more_matches(), test_member_never_sees_leader_chunks_on_any_path()

### Community 48 - "classify.py"
Cohesion: 0.38
Nodes (6): dataclasses, json, classify(), lexicon_hit(), Scope classifier, run before retrieval. off_scope -> polite decline. sensitive…, Verdict

### Community 49 - "FakeLLM"
Cohesion: 0.29
Nodes (4): install(), FakeLLM, _Obj, Scripted OpenAI-compatible client. `replies` consumed in order; a list reply…

### Community 50 - "test_ask_streams_and_persists"
Cohesion: 0.50
Nodes (4): sse(), test_ask_streams_and_persists(), test_conversations_are_private(), test_deleting_a_conversation_deletes_its_logs()

### Community 51 - "client"
Cohesion: 0.67
Nodes (3): client(), google(), fixture

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 336 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `connect`, `chat.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `process_source`, `embed.py`, `api/main.py`, `shepherd/__init__.py`, `run.py`, `Shepherd Guide: Build Guide in Phases`, `worker/main.py`, `retrieve.py`, `db.py`, `answer.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06956521739130435 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12222222222222222 - nodes in this community are weakly interconnected._
- **Should `embed.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11067193675889328 - nodes in this community are weakly interconnected._