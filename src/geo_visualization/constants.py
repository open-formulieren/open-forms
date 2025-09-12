"""
Constants for the RijksDriehoek (RD) schema (crs: EPSG:28992)

Source: https://api.pdok.nl/lv/bgt/ogc/v1/tileMatrixSets/NetherlandsRDNewQuad
"""

TILE_SIZE = 256

# PDOK origin of map
ORIGIN_X = -285401.92
ORIGIN_Y = 903401.92

# PDOK resolutions per zoom level
ZOOM_LEVEL_TO_RESOLUTION: dict[int, float] = {
    0: 3440.64,
    1: 1720.32,
    2: 860.16,
    3: 430.08,
    4: 215.04,
    5: 107.52,
    6: 53.76,
    7: 26.88,
    8: 13.44,
    9: 6.72,
    10: 3.36,
    11: 1.68,
    12: 0.84,
    13: 0.42,
    14: 0.21,
}
