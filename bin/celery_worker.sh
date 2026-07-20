#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}

QUEUE=${CELERY_WORKER_QUEUE:=celery}
WORKER_NAME=${CELERY_WORKER_NAME:="${QUEUE}"@%n}

# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openforms-worker-"${QUEUE}"}"
export CELERY_WORKER_MAX_TASKS_PER_CHILD=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-100}

echo "Starting celery worker $WORKER_NAME with queue $QUEUE"
# unset this if NOT using a process pool
export \
    _OTEL_DEFER_SETUP="true" \
    _TIMELINE_LOGGER_DEFER_LISTENER="true" \
    _LOG_OUTGOING_REQUESTS_LOGGER_DEFER_LISTENER="true"
exec celery --workdir src --app openforms.celery worker \
    -Q $QUEUE \
    -n $WORKER_NAME \
    -l $LOGLEVEL \
    -O fair \
    -c $CONCURRENCY
