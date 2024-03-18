CREATE USER objecttypes;
CREATE DATABASE objecttypes;
GRANT ALL PRIVILEGES ON DATABASE objecttypes TO objecttypes;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO objecttypes;

CREATE USER objects;
CREATE DATABASE objects;
GRANT ALL PRIVILEGES ON DATABASE objects TO objects;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO objects;
