-- Email + password sign-in for the chat app (scrypt hash, see api/chat.py).
alter table users add column password_hash text;
