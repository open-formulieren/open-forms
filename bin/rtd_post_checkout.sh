#!/bin/bash
#
# fetch the changelog from the SDK repository to include it in the build.
#
# RTD Docs: https://docs.readthedocs.io/en/stable/environment-variables.html
#

# default to the version in .sdk-release file
SDK_REF=$(cat .sdk-release | tr -d '[:space:]')

case $READTHEDOCS_VERSION_TYPE in
  # external = PR
  external) SDK_REF=main;;
  unknown) SDK_REF=main;;
esac

[ "$READTHEDOCS_VERSION_NAME" == "latest" ] && SDK_REF=main

URL="https://github.com/open-formulieren/open-forms-sdk/raw/${SDK_REF}/CHANGELOG.rst"

# download file from github and write it in the expected location
wget $URL -O docs/changelog-sdk.rst
