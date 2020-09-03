#!/bin/bash
#
# Build and push the docker image to Docker Hub.
#
# Usage: ./bin/docker_push.sh [image_tag]
#

# error on unset variables, exit on error
set -eu
set +x

# Login to Docker Hub
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Echo script commands
set -x

REPO=maykinmedia/openforms
TAG=${1:-latest}

# Build the image
docker build \
    -t $REPO:$TAG \
    .

# Push the image
docker push $REPO:$TAG
