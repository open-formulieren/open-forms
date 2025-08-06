#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}

QUEUE=${CELERY_WORKER_QUEUE:=celery}
WORKER_NAME=${CELERY_WORKER_NAME:="${QUEUE}"@%n}

# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openforms-worker-"${QUEUE}"}"

_binary=$(which celery)

if [[ "$ENABLE_COVERAGE" ]]; then
    _binary="coverage run $_binary"
fi

echo "Starting celery worker $WORKER_NAME with queue $QUEUE"
exec $_binary --workdir src --app openforms.celery worker \
    -Q $QUEUE \
    -n $WORKER_NAME \
    -l $LOGLEVEL \
    -O fair \
    -c $CONCURRENCY
