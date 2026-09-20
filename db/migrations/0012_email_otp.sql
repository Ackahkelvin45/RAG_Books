-- Email sign-ups must confirm a 6-digit code before the profile step.
-- Google accounts are verified by Google. Existing accounts are grandfathered in.
alter table users add column email_verified boolean not null default false;
update users set email_verified = true;

create table email_otps (
  user_id      uuid primary key references users(id) on delete cascade,
  code_hash    text not null,
  expires_at   timestamptz not null,
  attempts     int not null default 0,
  last_sent_at timestamptz not null default now()
);
grant select, insert, update, delete on email_otps to shepherd_app;
