-- Shepherd Guide schema, phase 1 (books only).
-- Single church deployment (First Love Church) — no multitenancy.

create extension if not exists vector;
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table users (
  id          uuid primary key default gen_random_uuid(),
  email       text not null unique,
  role        text not null check (role in ('leader', 'member', 'admin')),
  created_at  timestamptz not null default now()
);

create table sources (
  id          uuid primary key default gen_random_uuid(),
  type        text not null default 'book' check (type in ('book')),
  title       text not null,
  author      text,
  series      text,
  date        date,
  visibility  text not null default 'leader' check (visibility in ('leader', 'member')),
  file_uri    text not null,
  status      text not null default 'pending'
              check (status in ('pending', 'processing', 'ready', 'failed', 'superseded')),
  failure_reason text,
  version     int not null default 1,
  superseded_by uuid references sources(id),
  meta        jsonb not null default '{}',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table chunks (
  id          uuid primary key default gen_random_uuid(),
  source_id   uuid not null,
  content     text not null,                  -- enriched text, used for embedding + FTS
  raw_content text not null,                  -- verbatim text, shown to users
  embedding   vector(1024),                   -- bge-m3
  ts_doc      tsvector generated always as (to_tsvector('english', content)) stored,
  location    jsonb not null,                 -- {chapter, page, title}
  scripture   bigint[] not null default '{}', -- pythonbible verse ids
  token_count int,
  created_at  timestamptz not null default now(),
  foreign key (source_id) references sources(id) on delete cascade
);

create index chunks_embedding_idx on chunks using hnsw (embedding vector_cosine_ops);
create index chunks_ts_doc_idx   on chunks using gin (ts_doc);
create index chunks_scripture_idx on chunks using gin (scripture);
create index chunks_source_idx on chunks (source_id);

create table query_logs (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid references users(id),
  question       text not null,
  classification text check (classification in ('answerable', 'refused', 'redirected', 'off_scope')),
  language       text,
  retrieved_ids  uuid[],
  answer         text,
  prompt_version text,
  created_at     timestamptz not null default now(),
  expires_at     timestamptz not null default now() + interval '180 days'
);
create index query_logs_expires_idx on query_logs (expires_at);

create table eval_items (
  id                 uuid primary key default gen_random_uuid(),
  question           text not null,
  language           text not null default 'en' check (language in ('en', 'tw', 'mixed')),
  expected           text not null check (expected in ('answerable', 'refuse', 'redirect')),
  expected_source_id uuid references sources(id),
  note               text
);
create index eval_items_lookup_idx on eval_items (expected, language);

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------

create or replace function set_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

create trigger sources_updated_at before update on sources
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- Login lookup. Owned by the migration role, which the app role is not.
-- ---------------------------------------------------------------------------

create or replace function auth_lookup_user(p_email text)
returns table (user_id uuid, role text)
language sql security definer stable
set search_path = public as $$
  select u.id, u.role
  from users u
  where lower(u.email) = lower(p_email)
$$;

-- ---------------------------------------------------------------------------
-- Application role privileges (role itself is created outside migrations)
-- ---------------------------------------------------------------------------

grant usage on schema public to shepherd_app;
grant select, insert, update, delete on
  users, sources, chunks, query_logs, eval_items to shepherd_app;
grant execute on function auth_lookup_user(text) to shepherd_app;
