#!/bin/bash

#
# Compile the dependencies for production, CI and development.
#
# Usage, in the root of the project:
#
#     ./bin/compile_dependencies.sh
#
# Any extra flags/arguments passed to this wrapper script are passed down to pip-compile.
# E.g. to update a package:
#
#     ./bin/compile_dependencies.sh --upgrade-package django

set -ex

toplevel=$(git rev-parse --show-toplevel)

cd $toplevel

export CUSTOM_COMPILE_COMMAND="./bin/compile_dependencies.sh"

# Base (& prod) deps
pip-compile "$@" requirements/base.in

# Dependencies for testing
pip-compile \
    --output-file requirements/ci.txt \
    "$@" \
    requirements/test-tools.in \
    requirements/docs.in

# Type checking deps - CI + stub packages
pip-compile \
    --output-file requirements/type-checking.txt \
    "$@" \
    requirements/type-checking.in

# Dev dependencies - exact same set as CI + some extra tooling
pip-compile \
    --output-file requirements/dev.txt \
    "$@" \
    requirements/dev.in

# Dependencies for custom extensions
pip-compile \
    --output-file requirements/extensions.txt \
    "$@" \
    requirements/extensions.in
