#!/bin/sh

set -ex

fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

uwsgi_port=${UWSGI_PORT:-8000}
uwsgi_processes=${UWSGI_PROCESSES:-4}
uwsgi_threads=${UWSGI_THREADS:-1}

mountpoint=${SUBPATH:-/}

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# wait for required services
${SCRIPTPATH}/wait_for_db.sh

# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openforms}"

# Apply database migrations
>&2 echo "Apply database migrations"
python src/manage.py migrate

# Start server
>&2 echo "Starting server"
exec uwsgi \
    --strict \
    --listen 10 \
    --ini "${SCRIPTPATH}/uwsgi.ini" \
    --http :$uwsgi_port \
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
    --need-app \
    --processes $uwsgi_processes \
    --threads $uwsgi_threads \
    --post-buffering=8192 \
    --buffer-size=65535
    # processes & threads are needed for concurrency without nginx sitting inbetween
