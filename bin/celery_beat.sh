#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

mkdir -p celerybeat

echo "Starting celery beat"
exec celery beat \
    --app openforms \
    -l $LOGLEVEL \
    --workdir src \
    -s ../celerybeat/beat \
    --pidfile=  # empty on purpose, see #1182

