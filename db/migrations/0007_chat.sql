-- Product pivot (2026-09-19): users are shepherds and pastors only; no members,
-- no redirect-to-shepherd. They chat with the tool, and conversations persist.

drop function if exists shepherd_for(uuid);
drop index if exists users_one_default_contact;
alter table users drop column shepherd_id, drop column default_contact;

create table conversations (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users(id),
  title       text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index conversations_user_idx on conversations (user_id, updated_at desc);

create table messages (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  role            text not null check (role in ('user', 'assistant')),
  content         text not null,
  citations       jsonb not null default '[]',
  created_at      timestamptz not null default now()
);
create index messages_conv_idx on messages (conversation_id, created_at);

create trigger conversations_updated_at before update on conversations
  for each row execute function set_updated_at();

grant select, insert, update, delete on conversations, messages to shepherd_app;
