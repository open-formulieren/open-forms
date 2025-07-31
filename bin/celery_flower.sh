#!/bin/bash
# Set defaults for OTEL
: "${OTEL_SERVICE_NAME:=openforms-flower}"

exec celery --app openforms --workdir src flower
