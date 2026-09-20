-- Greetings, thanks and small talk ("hi", "thank you") get a short friendly reply, not the help text.
alter table query_logs drop constraint query_logs_classification_check;
alter table query_logs add constraint query_logs_classification_check
  check (classification in ('answerable', 'refused', 'redirected', 'off_scope', 'help', 'chat'));
