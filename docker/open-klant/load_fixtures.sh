#!/bin/sh

set -ex

# wait for migrations to be finished
until /app/src/manage.py migrate --check; do
    echo 'Waiting for migrations completion...'
    sleep 3
done

/app/src/manage.py loaddata /app/fixtures/open_klant_fixtures.json

echo "Done."
