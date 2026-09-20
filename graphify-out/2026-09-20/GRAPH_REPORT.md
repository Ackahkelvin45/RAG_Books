# Graph Report - RAG_sheperd  (2026-09-20)

## Corpus Check
- 93 files · ~42,511 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 795 nodes · 1545 edges · 34 communities (27 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- epub.py
- chunk_text
- Chat.tsx
- test_answer.py
- questions.py
- api/main.py
- test_portal.py
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
- classify.py
- emails.py
- entrypoint.sh
- retrieve.py
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
- `lifespan()` --calls--> `get_reranker()`  [INFERRED]
  api/main.py → shared/shepherd/rerank.py

## Import Cycles
- None detected.

## Communities (34 total, 7 thin omitted)

### Community 0 - "epub.py"
Cohesion: 0.09
Nodes (30): BeautifulSoup, boto3, botocore_exceptions, bs4, ebooklib, EpubBook, pathlib, bucket() (+22 more)

### Community 1 - "chunk_text"
Cohesion: 0.14
Nodes (17): Chunk, chunk_text(), flush(), Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens(), Embedder, Protocol (+9 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (50): react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError, ask() (+42 more)

### Community 3 - "test_answer.py"
Cohesion: 0.06
Nodes (58): datetime, ask_item(), cited_sentences(), eval_user(), generate(), injection(), judge(), load_items() (+50 more)

### Community 4 - "questions.py"
Cohesion: 0.28
Nodes (8): concurrent_futures, fill_batch(), _main(), Questions each passage answers (improvement stage 4). DeepSeek writes 3-5…, Generate, embed and store questions for up to `batch` chunks. Returns how many…, write_questions(), fill_questions(), Idle work: questions for chunks that have none (new books). 0 when there is…

### Community 5 - "api/main.py"
Cohesion: 0.11
Nodes (34): activity(), add_user(), admin(), books(), delete_book(), delete_user(), flash(), login() (+26 more)

### Community 6 - "test_portal.py"
Cohesion: 0.06
Nodes (29): contextlib, applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, fastapi_testclient, httpx (+21 more)

### Community 7 - "answer.py"
Cohesion: 0.11
Nodes (26): events(), ask(), attribution(), _citation(), _format_passages(), generate(), _history(), _main() (+18 more)

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
Cohesion: 0.09
Nodes (35): FakeEmbedder, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for…, add_source(), make_epub(), Path, Phase 2 acceptance: EPUB -> ready, failure -> failed + reason, reingest…, A failure mid-ingest rolls back: no chunks, status still recoverable., status_and_chunks() (+27 more)

### Community 12 - "scripture.py"
Cohesion: 0.13
Nodes (21): pythonbible, _main(), book_range(), chapter_range(), extract_verse_ids(), format_reference(), Scripture reference extraction and formatting, via pythonbible. Verse ids are…, All verse ids referenced in `text`, sorted and de-duplicated. (+13 more)

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
Cohesion: 0.20
Nodes (15): db(), db(), argparse, connect(), Open a connection as the restricted application role., sys, cmd_add(), cmd_add_dir() (+7 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.10
Nodes (18): 1. First deployment, 2. Moving the library from the development machine, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide, Admin portal (api/) (+10 more)

### Community 18 - "ingest.py"
Cohesion: 0.16
Nodes (13): Exception, logging, psycopg, Database access helpers. The app connects as the restricted `shepherd_app`…, Shared code for the Shepherd Guide API, worker, and eval harness., traceback, parse_file(), Path (+5 more)

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
Cohesion: 0.06
Nodes (53): BgeM3Embedder, get_embedder(), _join(), keyword_candidates(), merge_neighbours(), named_books(), names_title(), Connection (+45 more)

### Community 29 - "classify.py"
Cohesion: 0.29
Nodes (8): json, OpenAI, classify(), lexicon_hit(), Scope classifier, run before retrieval. off_scope -> polite decline. sensitive…, Verdict, client(), One OpenAI-compatible client pointed at DeepSeek. Tests swap `client()` via…

### Community 35 - "emails.py"
Cohesion: 0.43
Nodes (6): html, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 40 - "retrieve.py"
Cohesion: 0.11
Nodes (18): collections, dataclasses, functools, hashlib, os, re, Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Pinned models and environment-derived settings. One place to change them. (+10 more)

### Community 41 - "test_questions.py"
Cohesion: 0.28
Nodes (6): pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable()

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 315 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `connect`, `chat.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `test_answer.py`, `questions.py`, `api/main.py`, `answer.py`, `retrieve.py`, `Shepherd Guide: Build Guide in Phases`, `test_ingest.py`, `scripture.py`, `ingest.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `epub.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0928030303030303 - nodes in this community are weakly interconnected._
- **Should `chunk_text` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06956521739130435 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05874125874125874 - nodes in this community are weakly interconnected._