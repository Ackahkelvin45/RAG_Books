# Graph Report - RAG_sheperd  (2026-09-19)

## Corpus Check
- 91 files · ~40,834 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 4, .example 1, .jsonl 1)

## Summary
- 781 nodes · 1527 edges · 39 communities (33 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- connect
- test_ingest.py
- Chat.tsx
- test_answer.py
- embed.py
- api/main.py
- test_portal.py
- answer.py
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- os
- scripture.py
- Shepherd Guide: Phase One Implementation Handoff (v3, books-only)
- compilerOptions
- compilerOptions
- storage.py
- Shepherd Guide
- shepherd/__init__.py
- .oxlintrc.json
- React + TypeScript + Vite
- tsconfig.json
- CLAUDE.md
- 01_app_role.sh
- chat.py
- shepherd-guide
- test_retrieve.py
- retrieve.py
- questions.py
- named_books
- merge_neighbours
- llm.py
- classify.py
- emails.py
- _main
- chunking.py
- test_questions.py

## God Nodes (most connected - your core abstractions)
1. `transaction()` - 37 edges
2. `fake_llm()` - 27 edges
3. `connect()` - 21 edges
4. `retrieve()` - 20 edges
5. `signup()` - 20 edges
6. `compilerOptions` - 18 edges
7. `P()` - 17 edges
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
- `test_ministry_role_reaches_the_prompt()` --calls--> `_user()`  [INFERRED]
  tests/test_chat_api.py → shared/shepherd/answer.py
- `build_chunks()` --uses--> `Embedder`  [INFERRED]
  worker/ingest.py → shared/shepherd/embed.py

## Import Cycles
- None detected.

## Communities (39 total, 6 thin omitted)

### Community 0 - "connect"
Cohesion: 0.22
Nodes (14): db(), db(), argparse, connect(), Open a connection as the restricted application role., cmd_add(), cmd_add_dir(), cmd_list() (+6 more)

### Community 1 - "test_ingest.py"
Cohesion: 0.05
Nodes (69): BeautifulSoup, bs4, dataclasses, ebooklib, EpubBook, Exception, hashlib, pathlib (+61 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (51): epubjs, react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError (+43 more)

### Community 3 - "test_answer.py"
Cohesion: 0.06
Nodes (61): datetime, ask_item(), cited_sentences(), eval_user(), generate(), injection(), judge(), load_items() (+53 more)

### Community 4 - "embed.py"
Cohesion: 0.15
Nodes (8): BgeM3Embedder, Embedder, FakeEmbedder, get_embedder(), Protocol, Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a…, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for…, typing

### Community 5 - "api/main.py"
Cohesion: 0.14
Nodes (30): activity(), add_user(), admin(), books(), delete_book(), delete_user(), flash(), login() (+22 more)

### Community 6 - "test_portal.py"
Cohesion: 0.07
Nodes (27): applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, fastapi_testclient, io, psycopg, pytest (+19 more)

### Community 7 - "answer.py"
Cohesion: 0.14
Nodes (20): events(), ask(), attribution(), _citation(), _format_passages(), generate(), _history(), Grounded chat for shepherds and pastors (contract: handoff section 6, books… (+12 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.10
Nodes (30): client(), code_for(), email(), google(), fixture, parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup() (+22 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (32): oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript, vite (+24 more)

### Community 11 - "os"
Cohesion: 0.19
Nodes (8): os, BgeReranker, FakeReranker, get_reranker(), Protocol, Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-…, Fraction of query words present in the passage. Deterministic, no model., Reranker

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

### Community 16 - "storage.py"
Cohesion: 0.26
Nodes (12): boto3, botocore_exceptions, bucket(), _client(), delete(), download(), ensure_bucket(), open_book() (+4 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.18
Nodes (10): Admin portal (api/), API documentation (Swagger), Asking (phase 4), Chat app (web/, React + Vite), Ingesting a book (phase 2), Local setup, Scoring quality (eval/), Searching (phase 3) (+2 more)

### Community 18 - "shepherd/__init__.py"
Cohesion: 0.25
Nodes (5): contextlib, dotenv, Pinned models and environment-derived settings. One place to change them., Database access helpers. The app connects as the restricted `shepherd_app`…, Shared code for the Shepherd Guide API, worker, and eval harness.

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
Cohesion: 0.18
Nodes (18): keyword_candidates(), Connection, retrieve(), rrf(), ids_of(), Phase 3 acceptance: visibility leak test, scripture filtering, fusion, keyword…, A natural question with words absent from the passage must still match on the…, The leak test. Every candidate path is checked independently, then the full… (+10 more)

### Community 29 - "retrieve.py"
Cohesion: 0.20
Nodes (14): collections, _main(), question_candidates(), Hybrid retrieval: vector + keyword + generated-questions vector (+ scripture…, Fallback when the query is essentially just a reference and has no other words…, SQL fragment restricting sources by the caller's role. Fails closed for unknown…, Chunks whose generated questions are closest in meaning to the user's question., gather() (+6 more)

### Community 30 - "questions.py"
Cohesion: 0.20
Nodes (9): concurrent_futures, httpx, logging, Outgoing email via Resend (https://resend.com). Without RESEND_API_KEY the…, fill_batch(), _main(), Questions each passage answers (improvement stage 4). DeepSeek writes 3-5…, Generate, embed and store questions for up to `batch` chunks. Returns how many… (+1 more)

### Community 31 - "named_books"
Cohesion: 0.24
Nodes (10): named_books(), names_title(), Word lists a title may be written as: the whole title, and each part around ':'…, Ids of the visible books the query names by title., title_forms(), _named(), parametrize, test_a_named_book_is_recognised() (+2 more)

### Community 32 - "merge_neighbours"
Cohesion: 0.29
Nodes (8): _join(), merge_neighbours(), Concatenate adjacent chunks, dropping the overlap the chunker carried from…, Walk results best-first; a chunk next to one already taken (same book, same…, _p(), test_join_drops_the_carried_overlap(), test_merge_respects_chapter_and_cap(), test_neighbours_merge_in_reading_order_and_free_a_slot()

### Community 33 - "llm.py"
Cohesion: 0.33
Nodes (6): functools, OpenAI, One short, warm reply for greetings and thanks. Any failure falls back to a…, small_talk(), client(), One OpenAI-compatible client pointed at DeepSeek. Tests swap `client()` via…

### Community 34 - "classify.py"
Cohesion: 0.47
Nodes (5): json, classify(), lexicon_hit(), Scope classifier, run before retrieval. off_scope -> polite decline. sensitive…, Verdict

### Community 35 - "emails.py"
Cohesion: 0.43
Nodes (6): html, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 36 - "_main"
Cohesion: 0.40
Nodes (4): _main(), lookup_user_by_email(), Connection, Pre-auth lookup: email -> user/role, via the security-definer function.

### Community 40 - "chunking.py"
Cohesion: 0.25
Nodes (13): re, Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens() (+5 more)

### Community 41 - "test_questions.py"
Cohesion: 0.16
Nodes (11): pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable(), test_question_list_respects_visibility(), corpus() (+3 more)

## Knowledge Gaps
- **126 isolated node(s):** `01_app_role.sh script`, `shepherd-guide`, `$schema`, `plugins`, `react/rules-of-hooks` (+121 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 307 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `connect`, `chat.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `test_ingest.py`, `test_answer.py`, `_main`, `api/main.py`, `answer.py`, `Shepherd Guide: Build Guide in Phases`, `shepherd/__init__.py`, `retrieve.py`, `questions.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `shepherd-guide`, `$schema` to the rest of the system?**
  _126 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05063291139240506 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06800804828973843 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05541346973572037 - nodes in this community are weakly interconnected._
- **Should `api/main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13709677419354838 - nodes in this community are weakly interconnected._