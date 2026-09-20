-- Improvement stage 0: the eval harness and per-step query logging.

-- What each question is expected to do. 'redirect' went with the member pivot (0007).
alter table eval_items drop constraint eval_items_expected_check;
alter table eval_items add constraint eval_items_expected_check
  check (expected in ('answerable', 'refuse', 'off_scope', 'crisis', 'injection'));
alter table eval_items
  add column kind text not null default 'hand' check (kind in ('hand', 'generated')),
  -- the passage a generated question was written from; null for hand-written items
  add column expected_chunk_id uuid references chunks(id) on delete set null,
  -- {"earlier": [questions before this one], "inject": "text planted in a passage"}
  add column extra jsonb not null default '{}';
grant select, insert, update, delete on eval_items to shepherd_app;

-- What retrieval actually searched for and how sure the reranker was, so a
-- refusal threshold can be tuned from real traffic (retrieved_ids[i] scored scores[i]).
alter table query_logs
  add column retrieval_query text,
  add column scores real[],
  add column cited_ids uuid[];
