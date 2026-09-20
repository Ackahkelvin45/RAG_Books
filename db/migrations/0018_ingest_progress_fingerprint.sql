-- Improvement stage 7.
-- Progress of a book being processed, written from its own connection so the admin page can show
-- "embedding 340/820" while the ingest transaction is still open (the sources row is locked then).
create table ingest_progress (
  source_id  uuid primary key references sources(id) on delete cascade,
  message    text not null,
  updated_at timestamptz not null default now()
);
grant select, insert, update, delete on ingest_progress to shepherd_app;

-- Re-ingest reuses a passage's embedding, questions and question embedding when its text and the
-- embedding model are unchanged. Old rows have no fingerprint and are simply not reused.
alter table chunks add column fingerprint text;
create index chunks_fingerprint_idx on chunks (source_id, fingerprint);
