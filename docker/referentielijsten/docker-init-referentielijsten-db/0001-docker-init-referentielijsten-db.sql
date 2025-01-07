CREATE USER referentielijsten;
CREATE DATABASE referentielijsten;
GRANT ALL PRIVILEGES ON DATABASE referentielijsten TO referentielijsten;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO referentielijsten;
