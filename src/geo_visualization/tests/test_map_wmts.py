from unittest import TestCase

from shapely.geometry import shape

from ..typing import PolygonGeometry
from ..utils import find_maximum_zoom, geojson_to_rd


class WMTSMapTests(TestCase):
    def test_find_maximum_zoom_uses_fallback(self):
        # Note that this shape is half the size of the Netherlands
        value: PolygonGeometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    (3.856187, 51.807071),
                    (6.104054, 51.395801),
                    (6.008254, 52.525139),
                    (3.856187, 51.807071),
                ]
            ],
        }

        geometry = geojson_to_rd(shape(value))
        # We would need the lowest possible zoom level to fit this shape, so by setting
        # a custom minimum zoom, we ensure this value is used as a fallback
        zoom = find_maximum_zoom(geometry, (400, 300), min_zoom=5)

        self.assertEqual(zoom, 5)
