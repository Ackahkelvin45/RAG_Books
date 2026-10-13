-- A second embedding column, so a smaller model can be measured and switched to without
-- losing the bge-m3 vectors: SHEPHERD_EMBED_COLUMN picks which one retrieval reads.
-- 384 dims = bge-small-en-v1.5 (130 MB resident, against 2.2 GB for bge-m3).
alter table chunks add column embedding_small vector(384);
create index chunks_embedding_small_idx on chunks using hnsw (embedding_small vector_cosine_ops);
