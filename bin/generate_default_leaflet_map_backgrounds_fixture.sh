#!/bin/bash
#
# Dump the current (local database) config LeafletMapBackground to a JSON fixture.
# This overwrites the existing one.
#
# You can load this fixture with:
# $ src/manage.py loaddata default_leaflet_map_backgrounds
#
# Run this script from the root of the repository

src/manage.py dumpdata --indent=4 --natural-foreign --natural-primary config.LeafletMapBackground > src/openforms/fixtures/default_leaflet_map_backgrounds.json
