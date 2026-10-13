-- 'book' items: everyday-language questions written per book, so "did the right book come up"
-- is measured over 262 questions instead of the 30 hand-written ones (each of which was 3.3 points).
alter table eval_items drop constraint eval_items_kind_check;
alter table eval_items add constraint eval_items_kind_check
  check (kind in ('hand', 'generated', 'book'));
