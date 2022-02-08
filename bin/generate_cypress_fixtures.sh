#!/bin/bash

set -x

# Start a temporary container to produce the full fixture
docker-compose run -d -p 9999:8000 --name load-fixtures \
    --volume $(pwd)/src:/app/src \
    --volume $(pwd)/cypress/data_fixtures:/app/cypress/data_fixtures \
    web

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' localhost:9999)" != "403" ]]; do
    sleep 3;
done

docker exec --user root load-fixtures pip install factory-boy==3.0.1
docker exec --user root load-fixtures src/manage.py generate_cypress_fixtures

docker stop load-fixtures
docker rm load-fixtures
