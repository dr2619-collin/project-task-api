-- Local course-demo database setup. Run once with:
-- psql -d postgres -f scripts/setup_database.sql

CREATE ROLE postgres WITH LOGIN PASSWORD 'postgres';

CREATE DATABASE project_task
  OWNER postgres;
