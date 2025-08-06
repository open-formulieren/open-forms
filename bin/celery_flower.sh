#!/bin/bash
# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openforms-flower}"

exec celery --app openforms --workdir src flower
