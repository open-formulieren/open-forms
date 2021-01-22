#!/bin/bash
#
# Build the frontend so that Django can serve it, with the correct URL prefixes.
#

set -eu -o pipefail

toplevel=$(git rev-parse --show-toplevel)
cd $toplevel/src/spa

export REACT_APP_BASENAME=/demo-spa

yarn build --production
