#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "openzaak" <<-EOSQL
    CREATE EXTENSION postgis;
    CREATE EXTENSION pg_trgm;
EOSQL
