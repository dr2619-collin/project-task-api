-- Local development database setup. Run with:
-- psql -d postgres -f scripts/setup_database.sql

-- macOS Homebrew installations may not have a `postgres` user account yet,
-- while the Windows installer creates one during setup. Create it only when
-- it is absent.
SELECT 'CREATE ROLE postgres WITH LOGIN PASSWORD ''postgres'''
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'postgres'
)
\gexec

-- The database belongs to the local development user account. If it already exists, leave it
-- in place so students can safely rerun the script without deleting their work.
SELECT 'CREATE DATABASE project_task OWNER postgres'
WHERE NOT EXISTS (
  SELECT 1 FROM pg_database WHERE datname = 'project_task'
)
\gexec
