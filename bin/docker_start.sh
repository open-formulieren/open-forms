#!/bin/sh

set -ex

fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

mountpoint=${SUBPATH:-/}

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# Copy static root to volume, if required
if [ -n "$STATIC_ROOT_VOLUME" ]; then
    cp -r /app/static/* "$STATIC_ROOT_VOLUME"
fi

# wait for required services
${SCRIPTPATH}/wait_for_db.sh

# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openforms}"

# Apply database migrations
>&2 echo "Apply database migrations"
OTEL_SDK_DISABLED=True python src/manage.py migrate

export UWSGI_PROCESSES=${UWSGI_PROCESSES:-4}
export UWSGI_THREADS=${UWSGI_THREADS:-1}

# Periodically recycle workers - recover memory in the event of memory leaks
export UWSGI_MAX_REQUESTS=${UWSGI_MAX_REQUESTS:-1000}

# Start server
>&2 echo "Starting server"
exec uwsgi \
    --strict \
    --ini "${SCRIPTPATH}/uwsgi.ini" \
    --http :8000 \
    --http-keepalive \
    --mount $mountpoint=openforms.wsgi:application \
    --manage-script-name \
    --static-map /static=/app/static \
    --static-map /media=/app/media  \
    --chdir src \
    --enable-threads \
    --master \
    --single-interpreter \
    --die-on-term \
    --optimize 1 \
    --need-app \
    --post-buffering=8192 \
    --buffer-size=65535
    # processes & threads are needed for concurrency without nginx sitting inbetween
