#!/bin/bash

# setup initial configuration using environment variables
# Run this script from the root of the repository

set -e

if [[ "${RUN_SETUP_CONFIG,,}" =~ ^(true|1|yes)$ ]]; then
    # wait for required services
    ${SCRIPTPATH}/wait_for_db.sh

    if [[ "${SKIP_SELFTEST,,}" =~ ^(true|1|yes)$ ]]; then
        NO_SELFTEST_FLAG="--no-selftest"
    else
        NO_SELFTEST_FLAG=""
    fi

    src/manage.py migrate
    src/manage.py setup_configuration $NO_SELFTEST_FLAG \
                    --yaml-file data/services.yaml \
                    --yaml-file data/objects_api.yaml
fi
