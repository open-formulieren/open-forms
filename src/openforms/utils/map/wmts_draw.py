from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely.geometry import shape

from openforms.api.geojson import Coordinates, Geometry

# Constant values are from https://api.pdok.nl/lv/bgt/ogc/v1/tileMatrixSets/NetherlandsRDNewQuad
TILE_SIZE = 256
wgs84_to_rd_transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:28992", always_xy=True
)

# PDOK edges of map
ORIGIN_X = -285401.92
ORIGIN_Y = 903401.92

# PDOK resolutions per zoom level
RESOLUTIONS: dict[int, float] = {
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


def get_center(geojson: Geometry) -> tuple[float, float]:
    center = shape(geojson).centroid
    return center.x, center.y


def get_bounds_rd(geometry: Geometry) -> tuple[float, float, float, float]:
    """`geometry` should already be transformed from EPSG:4326 to EPSG:28992"""
    return shape(geometry).bounds


def geojson_to_rd(geojson: Geometry) -> Geometry:
    """
    Transform a geojson coordinates system to a RD (Rijksdriehoek) coordinates system.
    (EPSG:4326 to EPSG:28992)
    """

    def transform_coordinates_recursive(
        coordinates: Coordinates | list[Coordinates] | list[list[Coordinates]],
    ) -> Coordinates | list[Coordinates] | list[list[Coordinates]]:
        """
        The coordinates
        """
        if isinstance(coordinates[0], float):  # Point
            return wgs84_to_rd_transformer.transform(*coordinates)
        return [
            transform_coordinates_recursive(coordinate) for coordinate in coordinates
        ]

    new_geojson: Geometry = geojson.copy()
    new_geojson["coordinates"] = transform_coordinates_recursive(
        new_geojson["coordinates"]
    )
    return new_geojson


def find_best_zoom(
    bounds_rd: tuple[float, float, float, float],
    image_size_px: tuple[int, int],
    max_zoom: int = 14,
    min_zoom: int = 0,
    padding: float = 1.2,
) -> int:
    minx, miny, maxx, maxy = bounds_rd
    width_m = (maxx - minx) * padding
    height_m = (maxy - miny) * padding
    img_w_px, img_h_px = image_size_px

    for zoom in reversed(range(min_zoom, max_zoom + 1)):
        res = RESOLUTIONS[zoom]
        img_w_m = res * img_w_px
        img_h_m = res * img_h_px

        if img_w_m >= width_m and img_h_m >= height_m:
            return zoom

    return min_zoom  # fallback


def draw_geojson_rd(
    image: Image,
    geojson: Geometry,
    zoom: int,
    img_size: tuple[int, int],
    center_x_rd: float,
    center_y_rd: float,
) -> Image:
    """`geojson` should already be transformed to RD; from EPSG:4326 to EPSG:28992"""
    draw = ImageDraw.Draw(image)
    geom = shape(geojson)

    W, H = img_size
    res = RESOLUTIONS[zoom]

    def project_rd_to_pixel(x: int, y: int):
        dx = (x - center_x_rd) / res
        dy = (center_y_rd - y) / res  # Y axis reversed
        return (W / 2 + dx, H / 2 + dy)

    if geom.geom_type == "Point":
        x, y = project_rd_to_pixel(*geom.coords[0])
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill="red", outline="black")

    elif geom.geom_type == "LineString":
        points = [project_rd_to_pixel(*pt) for pt in geom.coords]
        draw.line(points, fill="green", width=3)

    elif geom.geom_type == "Polygon":
        exterior = [project_rd_to_pixel(*pt) for pt in geom.exterior.coords]
        draw.polygon(exterior, outline="blue", width=3, fill=None)

    return image
