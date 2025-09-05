from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely import transform
from shapely.geometry.base import BaseGeometry

from openforms.api.geojson import Coordinates
from openforms.utils.map.wmts_map_generator import px_to_rd

# Constant values are from https://api.pdok.nl/lv/bgt/ogc/v1/tileMatrixSets/NetherlandsRDNewQuad
TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)

# TODO-4951: convert to int rgb values?
SHAPE_COLOUR = "#3388ff"
POLYGON_FILL_ALPHA = "32" # 50% in hex
LINE_WIDTH = 3


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


def geojson_to_rd(geometry: BaseGeometry) -> BaseGeometry:
    """
    Transform a geojson coordinates system to a RD (Rijksdriehoek) coordinates system.
    (EPSG:4326 to EPSG:28992)
    """

    return transform(geometry, TRANSFORMER.transform, include_z=False, interleaved=False)



# TODO-4951: the bounds for a point need to be a little larger than the point itself,
#  because it's really unclear where you clicked in the summary - not enough context is
#  visible around the point. Note that this can also be achieved by increasing the
#  image size, as the zoom level will stay the same. Or by decreasing the maximum zoom
#  level -> probably the best solution
def find_best_zoom(
    geometry: BaseGeometry,
    image_size_px: tuple[int, int],
    max_zoom: int = 13,
    min_zoom: int = 0,
    padding: float = 1.2,
) -> int:
    """
    Find the best zoom level for which the geometry shape fits within the specified
    image size.

    A padding is applied to the geometry shape, to ensure there is some margin near the
    edges.

    :param geometry:
    :param image_size_px:
    :param max_zoom:
    :param min_zoom:
    :param padding:
    :return:
    """
    min_x, min_y, max_x, max_y = geometry.bounds
    width_m = (max_x - min_x) * padding
    height_m = (max_y - min_y) * padding
    img_w_px, img_h_px = image_size_px

    # Start at max zoom, because the shape is generally not large
    for zoom in range(max_zoom, min_zoom - 1, -1):
        # TODO-4951: a general converter to go switch between GPS coordinates, RD
        #  coordinates, and pixels might be nice
        # TODO-4951: it's probably more intuitive to transform the RD coords to their
        #  pixel equivalent?
        # Convert image size to RD coordinates
        img_w_m = px_to_rd(img_w_px, zoom)
        img_h_m = px_to_rd(img_h_px, zoom)
        # Ensure that the size of the image is larger than the size of the shape we are
        # trying to draw (in RD coordinates).
        if img_w_m >= width_m and img_h_m >= height_m:
            return zoom

    return min_zoom  # fallback


def draw_geojson_rd(
    image: Image,
    geometry: BaseGeometry,
    zoom: int,
    upsampling_factor: int = 4
) -> Image:
    """`geojson` should already be transformed to RD; from EPSG:4326 to EPSG:28992

    Note that we do not draw on the original image, but on a copy.
    """
    new_size = (image.size[0] * upsampling_factor, image.size[1] * upsampling_factor)
    image_upscaled = image.resize(new_size)

    geom_center_x, geom_center_y = geometry.centroid.coords[0]

    W, H = image.size
    res = RESOLUTIONS[zoom]
    def project_rd_to_pixel(x: int, y: int):
        dx = (x - geom_center_x) / res
        dy = (geom_center_y - y) / res  # Y axis reversed
        return (W / 2 + dx) * upsampling_factor, (H / 2 + dy) * upsampling_factor

    geometry_px = transform(
        geometry, project_rd_to_pixel, include_z=False, interleaved=False
    )

    if geometry_px.geom_type == "Point":
        radius = LINE_WIDTH * upsampling_factor
        x, y = geometry_px.coords[0]
        draw = ImageDraw.Draw(image_upscaled)
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=SHAPE_COLOUR,
            outline="black",
        )

    elif geometry_px.geom_type == "LineString":
        draw = ImageDraw.Draw(image_upscaled)
        draw.line(
            list(geometry_px.coords),
            fill=SHAPE_COLOUR,
            width=LINE_WIDTH * upsampling_factor
        )

    elif geometry_px.geom_type == "Polygon":
        overlay = Image.new("RGBA", image_upscaled.size)
        draw = ImageDraw.Draw(overlay)
        draw.polygon(
            list(geometry_px.exterior.coords),
            outline=SHAPE_COLOUR,
            width=LINE_WIDTH * upsampling_factor,
            fill=f"{SHAPE_COLOUR}{POLYGON_FILL_ALPHA}"
        )

        image_upscaled = Image.alpha_composite(image_upscaled, overlay)

    return image_upscaled.resize(image.size, Image.Resampling.HAMMING)
