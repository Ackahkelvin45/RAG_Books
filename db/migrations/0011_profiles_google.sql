-- Sign-up profile + Google sign-in.
-- ministry_role is what the person says they are (shown to the AI, visible to admins);
-- `role` stays the admin-controlled access level (leader-only books etc.).
alter table users
  add column first_name     text,
  add column last_name      text,
  add column date_of_birth  date,
  add column ministry_role  text check (ministry_role in ('member', 'shepherd', 'pastor')),
  add column google_sub     text unique;
