# Graph Report - RAG_sheperd  (2026-10-13)

## Corpus Check
- 97 files · ~44,138 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 806 nodes · 1573 edges · 40 communities (31 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `31067078`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_ingest.py
- chunking.py
- Chat.tsx
- test_answer.py
- embed.py
- api/main.py
- test_portal.py
- retrieve.py
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- ask
- scripture.py
- Shepherd Guide: Phase One Implementation Handoff (v3, books-only)
- compilerOptions
- compilerOptions
- connect
- Shepherd Guide
- db.py
- .oxlintrc.json
- React + TypeScript + Vite
- tsconfig.json
- CLAUDE.md
- 01_app_role.sh
- chat.py
- shepherd-guide
- Passage
- test_retrieve.py
- storage.py
- named_books
- app
- os
- test_mail.py
- emails.py
- entrypoint.sh
- Embedder
- rerank.py
- test_questions.py

## God Nodes (most connected - your core abstractions)
1. `transaction()` - 37 edges
2. `fake_llm()` - 28 edges
3. `connect()` - 22 edges
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
- `touch()` --calls--> `get_embedder()`  [INFERRED]
  api/main.py → shared/shepherd/embed.py
- `test_ministry_role_reaches_the_prompt()` --calls--> `_user()`  [INFERRED]
  tests/test_chat_api.py → shared/shepherd/answer.py

## Import Cycles
- None detected.

## Communities (40 total, 9 thin omitted)

### Community 0 - "test_ingest.py"
Cohesion: 0.05
Nodes (65): BeautifulSoup, bs4, ebooklib, EpubBook, Exception, logging, context_header(), enrich() (+57 more)

### Community 1 - "chunking.py"
Cohesion: 0.27
Nodes (12): Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens(), test_overlap_repeats_tail_of_previous_chunk() (+4 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (51): epubjs, react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError (+43 more)

### Community 3 - "test_answer.py"
Cohesion: 0.05
Nodes (63): datetime, ask_item(), cited_sentences(), eval_user(), generate(), generate_books(), injection(), judge() (+55 more)

### Community 4 - "embed.py"
Cohesion: 0.13
Nodes (13): concurrent_futures, hashlib, BgeM3Embedder, FakeEmbedder, get_embedder(), Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a…, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for…, fill_batch() (+5 more)

### Community 5 - "api/main.py"
Cohesion: 0.13
Nodes (31): activity(), add_user(), admin(), books(), delete_book(), delete_user(), flash(), login() (+23 more)

### Community 6 - "test_portal.py"
Cohesion: 0.25
Nodes (7): fastapi_testclient, login(), Admin portal smoke tests: auth gate, upload validation, book and user lifecycle., test_activity_renders(), test_book_upload_visibility_and_delete(), test_upload_rejects_other_file_types(), test_user_lifecycle()

### Community 7 - "retrieve.py"
Cohesion: 0.15
Nodes (18): collections, dataclasses, functools, json, OpenAI, re, Grounded chat for shepherds and pastors (contract: handoff section 6, books…, One short, warm reply for greetings and thanks. Any failure falls back to a… (+10 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.10
Nodes (30): client(), code_for(), email(), google(), fixture, parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup() (+22 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (32): oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript, vite (+24 more)

### Community 11 - "ask"
Cohesion: 0.12
Nodes (14): ask(), attribution(), _history(), _main(), Scriptures referenced: Romans 8:28; John 3:16-17.' from the cited passages only., The newest messages that fit HISTORY_CHARS, oldest first, never starting on an…, What retrieval searches for. The eval harness calls this too, so it measures…, Full request path. First event: {'type':'conversation', 'id':...}; then… (+6 more)

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
Cohesion: 0.15
Nodes (19): events(), db(), db(), argparse, connect(), lookup_user_by_email(), Connection, Open a connection as the restricted application role. (+11 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.10
Nodes (19): 1. First deployment, 2. Moving the library from the development machine, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide, Using your own nginx instead of Caddy (+11 more)

### Community 18 - "db.py"
Cohesion: 0.19
Nodes (10): contextlib, applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, io, psycopg (+2 more)

### Community 19 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 24 - "chat.py"
Cohesion: 0.05
Nodes (68): Ask, ask_endpoint(), auth_config(), book_file(), check_password(), Citation, Code, conversation() (+60 more)

### Community 28 - "Passage"
Cohesion: 0.19
Nodes (13): _citation(), _format_passages(), generate(), Stream {'type':'text'} events, then one {'type':'citations'} event., _join(), merge_neighbours(), Passage, Concatenate adjacent chunks, dropping the overlap the chunker carried from… (+5 more)

### Community 29 - "test_retrieve.py"
Cohesion: 0.13
Nodes (26): keyword_candidates(), Connection, question_candidates(), Fallback when the query is essentially just a reference and has no other words…, Chunks whose generated questions are closest in meaning to the user's question., retrieve(), gather(), rrf() (+18 more)

### Community 30 - "storage.py"
Cohesion: 0.23
Nodes (13): boto3, botocore_exceptions, pathlib, bucket(), _client(), delete(), download(), ensure_bucket() (+5 more)

### Community 31 - "named_books"
Cohesion: 0.20
Nodes (12): named_books(), names_title(), Word lists a title may be written as: the whole title, and each part around ':'…, Ids of the visible books the query names by title., SQL fragment restricting sources by the caller's role. Fails closed for unknown…, title_forms(), visibility_clause(), _named() (+4 more)

### Community 32 - "app"
Cohesion: 0.18
Nodes (11): admin(), app(), isolate_sources(), fixture, Superuser connection. Used only to set up and tear down fixtures., Restricted application role., Every source (and its chunks, via cascade) created during a test is removed…, One throwaway source with one chunk. (+3 more)

### Community 33 - "os"
Cohesion: 0.22
Nodes (6): httpx, os, Outgoing email via Resend (https://resend.com). Without RESEND_API_KEY the…, time, main(), Fill the configured embedding column for every chunk that is missing it.…

### Community 35 - "emails.py"
Cohesion: 0.43
Nodes (6): html, _app_url(), _layout(), otp_email(), Email templates. Each returns (subject, text, html). HTML is table-based with…, welcome_email()

### Community 40 - "rerank.py"
Cohesion: 0.16
Nodes (12): Load the embedding and reranking models at startup (~45 s), not on the first…, _warm_models(), keep_warm(), lifespan(), touch(), BgeReranker, FakeReranker, get_reranker() (+4 more)

### Community 41 - "test_questions.py"
Cohesion: 0.16
Nodes (11): pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable(), test_question_list_respects_visibility(), corpus() (+3 more)

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 320 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `connect`, `chat.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `test_ingest.py`, `os`, `test_answer.py`, `embed.py`, `api/main.py`, `retrieve.py`, `Shepherd Guide: Build Guide in Phases`, `ask`, `scripture.py`, `db.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.054414414414414414 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06800804828973843 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05472837022132797 - nodes in this community are weakly interconnected._
- **Should `embed.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13157894736842105 - nodes in this community are weakly interconnected._