-- Claim one pending source for the worker. `for update skip locked` lets
-- multiple workers run concurrently without double-claiming.

create or replace function claim_pending_source()
returns uuid
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
