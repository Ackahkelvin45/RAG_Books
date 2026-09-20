-- Stage 3 result: the reranker scores relevance, not whether a passage supports a sentence.
-- Calibrated against the DeepSeek judge (1,317 citations) it flagged more good citations than bad
-- at every threshold, so the live check was removed. Citation support stays an eval metric.
alter table query_logs drop column citation_checks;
