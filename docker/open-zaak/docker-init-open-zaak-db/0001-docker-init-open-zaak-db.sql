CREATE USER openzaak;
CREATE DATABASE openzaak OWNER openzaak;
GRANT ALL PRIVILEGES ON DATABASE openzaak TO openzaak;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO openzaak;
