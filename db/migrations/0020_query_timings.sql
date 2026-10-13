-- How long each question actually took, so slowness is a query rather than a hand measurement.
-- search_ms covers embed + candidate SQL + rerank; answer_ms is the DeepSeek stream.
alter table query_logs
  add column search_ms int,
  add column answer_ms int;
