from django.test import SimpleTestCase

from .wmts_draw import geojson_to_rd
from .wmts_map_generator import WMTSMapGenerator
from shapely.geometry import shape

class MapGeneratorTests(SimpleTestCase):
    def test_rd_to_tile(self):
        value = {
            "type": "Point",
            "coordinates": [5.291266, 52.1326332]
        }

        geometry = shape(value)
        geometry_rd = geojson_to_rd(geometry)

        x_rd, y_rd = geometry_rd.centroid.coords[0]

        x, y = WMTSMapGenerator.convert_rd_coordinate_to_tile(x_rd, y_rd, 13)
        print(x, y)

        x, y = WMTSMapGenerator.convert_rd_coordinate_to_pixel_in_tile(x_rd, y_rd, 13)
        print(x, y)

    def test_make_map_rd(self):
        value = {
            "type": "Point",
            "coordinates": [5.291266, 52.1326332]
        }

        geometry = shape(value)
        geometry_rd = geojson_to_rd(geometry)

        WMTSMapGenerator.make_map_rd(
            "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png",
            geometry_rd.centroid,
            13,
            (400, 300),
        )

