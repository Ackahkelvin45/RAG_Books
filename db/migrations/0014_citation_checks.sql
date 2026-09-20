-- Improvement stage 3: every cited sentence is scored against the passage it cites (reranker,
-- 0..1). [{"n": 2, "sentence": "...", "score": 0.91}, ...]; empty when nothing was cited.
alter table query_logs add column citation_checks jsonb not null default '[]';
