CREATE USER openforms;
CREATE DATABASE openforms;
GRANT ALL PRIVILEGES ON DATABASE openforms TO openforms;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO openforms;
