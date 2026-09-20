-- claim_pending_source() returned a scalar uuid, so an empty queue yielded one
-- NULL row and the worker "claimed" nothing. Return a set instead: zero rows
-- when idle. Return type changes need drop + create.

drop function if exists claim_pending_source();

create function claim_pending_source()
returns setof uuid
language sql volatile
set search_path = public as $$
  update sources s
     set status = 'processing'
   where s.id = (
     select id from sources
      where status = 'pending'
      order by created_at
      for update skip locked
      limit 1)
  returning s.id
$$;

grant execute on function claim_pending_source() to shepherd_app;
