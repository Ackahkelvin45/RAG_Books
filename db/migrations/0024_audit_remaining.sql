-- Audit 2026-10-14, remaining items.
-- category: the classifier's sensitive category, so the admin activity page can show the kind of question
-- without its text. conversation_id: deleting a conversation deletes its question logs too.
alter table query_logs add column category text, add column conversation_id uuid;
create index query_logs_conversation_idx on query_logs (conversation_id);

-- 'user': real questions exported from production and labelled by a person (README, scoring quality).
alter table eval_items drop constraint eval_items_kind_check;
alter table eval_items add constraint eval_items_kind_check check (kind in ('hand', 'generated', 'book', 'user'));
