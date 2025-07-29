#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

# Set defaults for OTEL
: "${OTEL_SERVICE_NAME:=openforms-beat}"

mkdir -p celerybeat

echo "Starting celery beat"
exec celery --app openforms  --workdir src beat \
    -l $LOGLEVEL \
    -s ../celerybeat/beat \
    --pidfile=  # empty on purpose, see #1182

