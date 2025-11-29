#!/bin/bash
#
# Sets the Github action output variable for the SDK version to build/include. Requires
# the repo to be checked out and the script to be called from the repository root.
#
# Usage:
#
#   ./extract_sdk_version.sh <backend-version> <base-ref>

# Translate args into variables
backend_version=$1
base_ref=$2

# default to version in .sdk-release file
SDK_VERSION=$(cat .sdk-release | tr -d '[:space:]')

# PRs have the base_ref, straight up pushes don't
if [[ "$base_ref" == stable/* ]]; then
    echo "pull request to stable branch"
else
    echo "not a pull request to a stable branch"
    [[ "$backend_version" == latest ]] && SDK_VERSION=latest
fi

# Translate the version into the git ref of the open-forms-sdk repository.
SDK_REF=$SDK_VERSION
[[ "$SDK_VERSION" == latest ]] && SDK_REF=main

echo "sdk-version=${SDK_VERSION}" >> $GITHUB_OUTPUT
echo "sdk-ref=${SDK_REF}" >> $GITHUB_OUTPUT
