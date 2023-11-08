#!/bin/bash

set -eu -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sitepackagesdir=${1:-}
if [[ -z "$sitepackagesdir" ]]; then
    echo "You must provide the path to site-packages";
    exit 1;
fi

cd $sitepackagesdir
echo "Patching packages in: $(pwd)"

for patch_file in $SCRIPT_DIR/yubin_00{1..4}.patch
do
    echo "Applying patch file: $patch_file"
    git apply $patch_file
done

echo "Done patching."
