#!/bin/sh
#
# Automatically apply the HC BRP personen bevragen data patches when the container
# starts up.
#
# This relies on the main container providing the data fixture, and a one-time init
# container mounting the same volume to apply the patches.
#

set -eu -o pipefail

while [ ! -f /test-data/test-data.json ]; do
    echo 'test data file does not exist yet, waiting...'
    sleep 1
done

echo 'test-data.json file exists, proceeding with patching...'

cd /test-data/

for patch_file in /patches/*.patch; do
  rel_path=$(basename "$patch_file")
  if grep -Fxq "$rel_path" ./applied_patches.txt; then
    echo "Patch $rel_path is already applied."
  else
      echo "Applying patch: $rel_path..."
      git apply "$patch_file"
      echo "$rel_path" >> ./applied_patches.txt
  fi
done
