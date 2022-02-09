#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

mkdir -p celerybeat

echo "Starting celery beat"
exec celery --app openforms  --workdir src beat \
    -l $LOGLEVEL \
    -s ../celerybeat/beat \
    --pidfile=  # empty on purpose, see #1182

