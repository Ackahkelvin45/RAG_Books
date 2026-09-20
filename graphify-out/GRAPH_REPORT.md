# Graph Report - RAG_sheperd  (2026-09-20)

## Corpus Check
- 93 files · ~42,863 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 7, .example 2, .jsonl 1)

## Summary
- 797 nodes · 1549 edges · 40 communities (33 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cb00ffeb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_ingest.py
- chunking.py
- Chat.tsx
- test_answer.py
- embed.py
- api/main.py
- os
- answer.py
- test_chat_api.py
- Shepherd Guide: Build Guide in Phases
- package.json
- google_callback
- scripture.py
- Shepherd Guide: Phase One Implementation Handoff (v3, books-only)
- compilerOptions
- compilerOptions
- ask_endpoint
- Shepherd Guide
- SignUp
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
- Profile
- get
- login
- corpus
- entrypoint.sh
- _named
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
- `lifespan()` --calls--> `get_reranker()`  [INFERRED]
  api/main.py → shared/shepherd/rerank.py
- `test_ministry_role_reaches_the_prompt()` --calls--> `_user()`  [INFERRED]
  tests/test_chat_api.py → shared/shepherd/answer.py

## Import Cycles
- None detected.

## Communities (40 total, 7 thin omitted)

### Community 0 - "test_ingest.py"
Cohesion: 0.05
Nodes (60): BeautifulSoup, bs4, ebooklib, EpubBook, Exception, FakeEmbedder, Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for…, sys (+52 more)

### Community 1 - "chunking.py"
Cohesion: 0.17
Nodes (17): re, Chunk, chunk_text(), flush(), Recursive, chapter-bounded chunking. Paragraphs are packed into chunks of…, Paragraphs, with oversized paragraphs split into sentences., _units(), whitespace_tokens() (+9 more)

### Community 2 - "Chat.tsx"
Cohesion: 0.07
Nodes (51): epubjs, react, react-dom, AnswerText(), chapterLabel(), Sources(), api, ApiError (+43 more)

### Community 3 - "test_answer.py"
Cohesion: 0.06
Nodes (57): datetime, ask_item(), cited_sentences(), eval_user(), generate(), injection(), judge(), load_items() (+49 more)

### Community 4 - "embed.py"
Cohesion: 0.15
Nodes (9): Load the embedding and reranking models at startup (~45 s), not on the first…, _warm_models(), lifespan(), hashlib, BgeM3Embedder, Embedder, get_embedder(), Protocol (+1 more)

### Community 5 - "api/main.py"
Cohesion: 0.09
Nodes (49): activity(), add_user(), admin(), books(), delete_book(), delete_user(), flash(), login() (+41 more)

### Community 6 - "os"
Cohesion: 0.05
Nodes (36): contextlib, applied(), main(), Connection, Apply db/migrations/*.sql in order, once each. Usage: uv run python…, dotenv, fastapi_testclient, html (+28 more)

### Community 7 - "answer.py"
Cohesion: 0.06
Nodes (47): db(), db(), concurrent_futures, dataclasses, functools, json, logging, OpenAI (+39 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.10
Nodes (33): client(), code_for(), email(), google(), fixture, parametrize, Chat API: auth, conversation ownership, streaming ask, passage visibility. No…, signup() (+25 more)

### Community 9 - "Shepherd Guide: Build Guide in Phases"
Cohesion: 0.07
Nodes (28): Finished: what the first release looks like, Overview, Phase 1: Database foundation, Phase 2: EPUB book reading, Phase 3: Search, Phase 4: Safety check and answers, Phase 5: PDF book reading, Phase 6: Testing the answers (+20 more)

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (32): oxlint, react-markdown, remark-gfm, @types/node, @types/react, @types/react-dom, typescript, vite (+24 more)

### Community 11 - "google_callback"
Cohesion: 0.22
Nodes (11): auth_config(), current_user(), google_callback(), _google_conf(), google_start(), google_userinfo(), logout(), Request (+3 more)

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

### Community 16 - "ask_endpoint"
Cohesion: 0.22
Nodes (9): Ask, ask_endpoint(), events(), conversation(), delete_conversation(), EventStream, _own(), Runs the full pipeline: classify → search the books → answer from the passages… (+1 more)

### Community 17 - "Shepherd Guide"
Cohesion: 0.10
Nodes (19): 1. First deployment, 2. Moving the library from the development machine, 3. Updating, 4. Backups and restore, 5. Checking it works, 6. Running costs, Deploying Shepherd Guide, Using your own nginx instead of Caddy (+11 more)

### Community 18 - "SignUp"
Cohesion: 0.24
Nodes (10): Code, _otp_hash(), post, Creates a **member** account, signs the person in (session cookie) and emails a…, Create (or replace) the user's code and email it. Caller holds a transaction., Codes expire after 10 minutes. Five wrong tries lock the code until a new one…, resend_code(), send_otp() (+2 more)

### Community 19 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 24 - "chat.py"
Cohesion: 0.15
Nodes (17): Citation, ConversationSummary, Location, MessageOut, OK, PassageOut, JSON API for the React chat app (web/). Mounted under /api by api/main.py. Auth…, Everything past sign-up requires a confirmed email address. (+9 more)

### Community 28 - "test_retrieve.py"
Cohesion: 0.16
Nodes (19): _join(), merge_neighbours(), Connection, Concatenate adjacent chunks, dropping the overlap the chunker carried from…, Walk results best-first; a chunk next to one already taken (same book, same…, retrieve(), rrf(), _p() (+11 more)

### Community 29 - "test_member_never_sees_leader_chunks_on_any_path"
Cohesion: 0.21
Nodes (15): keyword_candidates(), question_candidates(), Fallback when the query is essentially just a reference and has no other words…, Chunks whose generated questions are closest in meaning to the user's question., gather(), scripture_candidates(), vector_candidates(), _where() (+7 more)

### Community 30 - "storage.py"
Cohesion: 0.26
Nodes (12): boto3, botocore_exceptions, bucket(), _client(), delete(), download(), ensure_bucket(), open_book() (+4 more)

### Community 31 - "retrieve.py"
Cohesion: 0.21
Nodes (12): collections, _main(), named_books(), names_title(), Hybrid retrieval: vector + keyword + generated-questions vector (+ scripture…, Word lists a title may be written as: the whole title, and each part around ':'…, Ids of the visible books the query names by title., SQL fragment restricting sources by the caller's role. Fails closed for unknown… (+4 more)

### Community 32 - "Profile"
Cohesion: 0.22
Nodes (7): Profile, Required once after sign-up. The first save also sends the welcome email., save_profile(), SignIn, date, field_validator, put

### Community 33 - "get"
Cohesion: 0.25
Nodes (8): book_file(), conversations(), Me, passage(), get, The app uses `email_verified` and `profile_complete` to decide which screen to…, What a citation link opens: the passage, its book and chapter, the verses it…, Streams the stored EPUB. `?download=1` sets a filename so the browser saves it.

### Community 34 - "login"
Cohesion: 0.25
Nodes (8): check_password(), hash_password(), login(), login_locked(), A success clears the account's failures; a failure adds one., Sets the session cookie. **In Swagger, call this first**; later \"Try it out\"…, record_login(), test_password_hash_roundtrip()

### Community 35 - "corpus"
Cohesion: 0.40
Nodes (4): corpus(), add_chunk(), fixture, One leader-only source and one member source, each with chunks and embeddings.

### Community 37 - "_named"
Cohesion: 0.67
Nodes (4): _named(), parametrize, test_a_named_book_is_recognised(), test_everyday_words_are_not_a_book()

### Community 40 - "rerank.py"
Cohesion: 0.19
Nodes (8): BgeReranker, FakeReranker, get_reranker(), Protocol, Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-…, Fraction of query words present in the passage. Deterministic, no model., Reranker, typing

### Community 41 - "test_questions.py"
Cohesion: 0.27
Nodes (7): pgvector_psycopg, ByPassage, _Obj, Stage 4: generated questions per chunk, and the retrieval list that searches…, Thread-safe fake: the reply depends on the passage, not on call order., test_fill_writes_questions_and_embedding_and_is_resumable(), test_question_list_respects_visibility()

## Knowledge Gaps
- **134 isolated node(s):** `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide`, `$schema`, `plugins` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 316 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `M1 — Schema, local infra` connect `Shepherd Guide: Build Guide in Phases` to `api/main.py`, `answer.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `connect()` connect `answer.py` to `test_ingest.py`, `test_answer.py`, `api/main.py`, `Shepherd Guide: Build Guide in Phases`, `ask_endpoint`, `retrieve.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `01_app_role.sh script`, `entrypoint.sh script`, `shepherd-guide` to the rest of the system?**
  _134 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05134575569358178 - nodes in this community are weakly interconnected._
- **Should `Chat.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06800804828973843 - nodes in this community are weakly interconnected._
- **Should `test_answer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06009615384615385 - nodes in this community are weakly interconnected._
- **Should `api/main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08686868686868687 - nodes in this community are weakly interconnected._