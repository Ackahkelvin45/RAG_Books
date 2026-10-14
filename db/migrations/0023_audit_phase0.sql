-- Audit 2026-10-14, phase 0: make every answer and eval run attributable to the models that produced it.
-- models: "<embed model>@<column>+<reranker>"; search_ms stays the total, the three parts let production
-- say where the time went; token counts come from the DeepSeek usage block.
alter table query_logs
  add column models text,
  add column embed_ms int,
  add column sql_ms int,
  add column rerank_ms int,
  add column prompt_tokens int,
  add column completion_tokens int,
  add column cached_tokens int;

-- bge-base-en-v1.5 (768 dims): the second candidate for the small server. The dev database already had the
-- column by hand, hence "if not exists"; production gets it here.
alter table chunks add column if not exists embedding_base vector(768);
create index if not exists chunks_embedding_base_idx on chunks using hnsw (embedding_base vector_cosine_ops);

-- The generated-question search list has been off since the 2026-09-19 eval (no gain on hand-written
-- questions). The worker no longer fills questions and the 107 MB index goes; the text stays, so the list
-- can be re-tested on real questions by recreating the index and setting SHEPHERD_QUESTION_SEARCH=on.
drop index if exists chunks_q_embedding_idx;
