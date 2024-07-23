#!/bin/sh

#
# Compile the dependencies for production, CI and development.
#
# Usage, in the root of the project:
#
#     ./bin/compile_dependencies.sh
#
# Any extra flags/arguments passed to this wrapper script are passed down to
# `uv pip compile`. E.g. to update a package:
#
#     ./bin/compile_dependencies.sh --upgrade-package django

set -ex

command -v uv || (echo "uv not found on PATH. Install it https://astral.sh/uv" >&2 && exit 1)

cwd="${PWD}"
toplevel=$(git rev-parse --show-toplevel)

cd $toplevel

export UV_CUSTOM_COMPILE_COMMAND="./bin/compile_dependencies.sh"

# Base (& prod) deps
uv pip compile \
    --output-file requirements/base.txt \
    "$@" \
    requirements/base.in

# Dependencies for testing
uv pip compile \
    --output-file requirements/ci.txt \
    "$@" \
    requirements/test-tools.in \
    requirements/docs.in

# Type checking deps - CI + stub packages
uv pip compile \
    --output-file requirements/type-checking.txt \
    "$@" \
    requirements/type-checking.in

# Dev dependencies - exact same set as CI + some extra tooling
uv pip compile \
    --output-file requirements/dev.txt \
    "$@" \
    requirements/dev.in

# Dependencies for custom extensions
uv pip compile \
    --output-file requirements/extensions.txt \
    "$@" \
    requirements/extensions.in

cd "${cwd}"
