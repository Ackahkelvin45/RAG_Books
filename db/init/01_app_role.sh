#!/bin/bash
# Runs once when the local Postgres volume is first created.
# Creates the restricted application role. In production, create this role
# by hand with a strong password; migrations only grant privileges to it.
set -e
psql -v ON_ERROR_STOP=1 --username postgres --dbname shepherd <<-SQL
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shepherd_app') THEN
      CREATE ROLE shepherd_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    END IF;
  END
  \$\$;
  ALTER ROLE shepherd_app PASSWORD '${APP_DB_PASSWORD}';
SQL
