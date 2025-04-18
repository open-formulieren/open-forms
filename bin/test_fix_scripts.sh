#!/bin/bash

set -eu -o pipefail

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $SCRIPTPATH

shopt -s nullglob

for script in fix_*.py; do
    echo "Checking $script ..."
    python "$script"
    echo "OK!"
done
