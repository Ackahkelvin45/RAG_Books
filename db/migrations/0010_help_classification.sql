-- "What can I ask you to do?" gets a fixed help answer; log it as its own class.
alter table query_logs drop constraint query_logs_classification_check;
alter table query_logs add constraint query_logs_classification_check
  check (classification in ('answerable', 'refused', 'redirected', 'off_scope', 'help'));
