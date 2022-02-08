#!/bin/bash

container=$(docker inspect -f '{{.Name}}' $(docker-compose ps -q web) | cut -c2-)

for filename in cypress/data_fixtures/_build/*.json; do
    cat "$filename" | docker exec -i $container src/manage.py loaddata --format=json -
done
