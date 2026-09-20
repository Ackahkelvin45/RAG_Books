-- Seed the admin user. Replace the email before first real login.
insert into users (email, role)
values ('admin@firstlove.example', 'admin')
on conflict (email) do nothing;
