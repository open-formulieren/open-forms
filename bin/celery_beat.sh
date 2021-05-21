#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

mkdir -p celerybeat

echo "Starting celery beat"
exec celery beat \
    --app bptl \
    -l $LOGLEVEL \
    --workdir src \
    -s ../celerybeat/beat
