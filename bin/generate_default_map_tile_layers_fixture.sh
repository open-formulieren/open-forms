#!/bin/bash
#
# Dump the current (local database) config MapTileLayer to a JSON fixture.
# This overwrites the existing one.
#
# You can load this fixture with:
# $ src/manage.py loaddata default_map_tile_layers
#
# Run this script from the root of the repository

src/manage.py dumpdata \
    --indent=4 \
    --natural-foreign \
    --natural-primary \
    config.MapTileLayer \
    > src/openforms/fixtures/default_map_tile_layers.json
