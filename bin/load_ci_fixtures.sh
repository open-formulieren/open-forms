#!/bin/bash

# Usage: bin/load_ci_fixtures.sh <container_name>

for filename in cypress/data_fixtures/*.json; do
    cat "$filename" | docker exec -i $1 src/manage.py loaddata --format=json -
done
