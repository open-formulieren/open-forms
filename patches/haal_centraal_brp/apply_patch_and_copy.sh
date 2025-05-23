#!/bin/bash

set -eu -o pipefail

# Container name
CONTAINER_NAME="personen-mock"

# Get absolute path of the script and patches directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PATCH_DIR="$SCRIPT_DIR"
PATCH_TARGET_FILENAME="test-data.json"
CONTAINER_DEST_PATH="/app/Data/$PATCH_TARGET_FILENAME"

# Get user-provided git-tracked directory where test-data.json lives
TARGET_WORKDIR=${1:-}

if [[ -z "$TARGET_WORKDIR" ]]; then
  echo "Usage: $0 <path-to-local-git-folder-containing-test-data.json>"
  echo "Example: $0 ./Data"
  exit 1
fi

TARGET_ABS_PATH=$(realpath "$TARGET_WORKDIR")
PATCH_TARGET_FILE="$TARGET_ABS_PATH/$PATCH_TARGET_FILENAME"

# Validations
[[ ! -d "$TARGET_ABS_PATH/.git" ]] && { echo "Error: $TARGET_ABS_PATH is not a Git repo."; exit 1; }
[[ ! -f "$PATCH_TARGET_FILE" ]] && { echo "Error: $PATCH_TARGET_FILENAME not found in $TARGET_ABS_PATH"; exit 1; }

# Apply patches
cd "$TARGET_ABS_PATH"
for patch_file in "$PATCH_DIR"/*.patch; do
  echo "Applying patch: $(basename "$patch_file")"
  git apply "$patch_file"
done
cd - > /dev/null

# Copy the patched file to the container
echo "Copying patched file to container..."
docker cp "$PATCH_TARGET_FILE" "$CONTAINER_NAME:$CONTAINER_DEST_PATH"

echo "Done! Patched test-data.json copied to container at $CONTAINER_DEST_PATH"
