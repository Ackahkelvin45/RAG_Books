-- Members use the app too (2026-09-19). Books are visible to everyone unless an
-- admin marks one leader-only.
alter table sources alter column visibility set default 'member';
update sources set visibility = 'member';
