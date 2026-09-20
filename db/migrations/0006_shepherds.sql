-- Shepherds and pastors are users. A member is linked to their shepherd, and a
-- redirect names that shepherd with their contact details. Contact is collected
-- at sign-up (phase 8 UI); until then set via SQL / CLI.

alter table users
  add column name        text,
  add column phone       text,                          -- how to reach them today
  add column shepherd_id uuid references users(id);     -- this user's shepherd

-- Church-wide fallback when a user has no shepherd yet (or the asker is anonymous):
-- the leader/admin flagged as the default contact.
alter table users add column default_contact boolean not null default false;
create unique index users_one_default_contact on users (default_contact) where default_contact;

create or replace function shepherd_for(p_user uuid)
returns table (name text, phone text)
language sql security definer stable
set search_path = public as $$
  select s.name, s.phone
    from users u join users s on s.id = u.shepherd_id
   where u.id = p_user and s.name is not null
  union all
  select name, phone from users where default_contact
  limit 1
$$;
grant execute on function shepherd_for(uuid) to shepherd_app;
