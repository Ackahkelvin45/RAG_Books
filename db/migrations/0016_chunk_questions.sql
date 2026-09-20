-- Improvement stage 4: questions each passage answers, written by DeepSeek, so everyday
-- wording ("my member keeps missing church") can match sermon prose. A third retrieval list
-- searches q_embedding. questions is null until generated; '' means the passage answers
-- nothing (a list, an acknowledgement) and has no q_embedding.
alter table chunks
  add column questions   text,
  add column q_embedding vector(1024);
create index chunks_q_embedding_idx on chunks using hnsw (q_embedding vector_cosine_ops);
