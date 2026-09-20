-- Failed sign-ins, for throttling password guessing. Keyed by lower-cased email (or 'admin-portal'),
-- not by IP: behind a proxy every visitor shares one address. Rows older than a day are purged by the worker.
create table login_failures (
  key text not null,
  at  timestamptz not null default now()
);
create index login_failures_key_at_idx on login_failures (key, at);
grant select, insert, delete on login_failures to shepherd_app;
