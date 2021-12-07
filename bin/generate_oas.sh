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

outfile=${1:-src/openapi.yaml}

src/manage.py spectacular \
    --validate \
    --fail-on-warn \
    --lang=en \
    --file "$outfile"
