#!/bin/bash

docker compose \
    -f docker-compose.generic-json.yml \
    -f docker-compose.hc-brp-mock.yml \
    -f docker-compose.keycloak.yml \
    -f docker-compose.objects-apis.yml \
    -f docker-compose.open-klant.yml \
    -f docker-compose.open-zaak.yml \
    -f docker-compose.referentielijsten.yml \
    -f docker-compose.rx-mission.yml \
    -f docker-compose.stuf-zds.yml \
    up
