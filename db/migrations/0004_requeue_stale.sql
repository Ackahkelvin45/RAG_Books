-- A worker that dies mid-ingest leaves its source in 'processing' forever.
-- Ingest is one transaction, so nothing partial exists; requeue after a timeout.
-- updated_at is bumped by trigger whenever status changes.

create or replace function requeue_stale_sources(p_older_than interval)
returns setof uuid
language sql volatile
set search_path = public as $$
  update sources
     set status = 'pending'
   where status = 'processing'
     and updated_at < now() - p_older_than
  returning id
$$;

grant execute on function requeue_stale_sources(interval) to shepherd_app;
