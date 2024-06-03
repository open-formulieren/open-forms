#!/bin/bash
#
# Generate the OpenAPI 3.x spec from the code using drf-spectacular.
#
# Invoke this script from the root of the project:
#
#   $ ./bin/generate_oas.sh [outfile]
#
# 'outfile' defaults to `src/openapi.yml``
#
set -eu -o pipefail

CI=${CI:-}

outfile=${1:-src/openapi.yaml}

if [[ -z "${CI}" ]]; then
    echo "Dumping local configuration..."
    CURRENT_CONFIG_FIXTURE=$(src/manage.py dumpdata config.GlobalConfiguration flags)
    echo "Disabling demo plugins..."
    src/manage.py disable_demo_plugins
fi

src/manage.py spectacular \
    --validate \
    --fail-on-warn \
    --lang=en \
    --file "$outfile"

# restore global config
if [[ -z "${CI}" ]]; then
    echo "Restoring local configuration..."
    echo $CURRENT_CONFIG_FIXTURE | src/manage.py loaddata --format=json -
fi

echo "Schema generated!"
