from base64 import b64encode
from io import BytesIO

from shapely.geometry import shape

from openforms.api.geojson import LineStringGeometry, PointGeometry, PolygonGeometry

from .constants import ZOOM_LEVEL_TO_RESOLUTION
from .utils import find_maximum_zoom, geojson_to_rd
from .wmts_draw import draw_geometry_on_map
from .wmts_map_generator import generate_map_image

__all__ = ["generate_map_image_with_geojson"]


type GEOJSON = PointGeometry | LineStringGeometry | PolygonGeometry


def generate_map_image_with_geojson(
    geojson: GEOJSON,
    url_template: str,
    image_size: tuple[int, int],
    max_zoom: int = max(ZOOM_LEVEL_TO_RESOLUTION),
) -> str | None:
    """
    Generate a map image with a geojson shape drawn onto it.

    :param geojson: The geojson shape to draw.
    :param url_template: URL template to load tiles from. This URL should be
      formattable with x, y, and z parameters. For example:
      https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png
    :param image_size: Image size in pixels (width, height).
    :param max_zoom: Maximum zoom level to use.
    :return: Image of the map in png format, encoded using base64. ``None`` if it could
      not be loaded.
    """
    geometry_rd = geojson_to_rd(shape(geojson))

    zoom = find_maximum_zoom(
        geometry=geometry_rd, max_zoom=max_zoom, image_size=image_size
    )

    map_img = generate_map_image(
        url_template=url_template,
        center=geometry_rd.centroid,
        zoom=zoom,
        img_size=image_size,
    )

    if map_img is None:
        return None

    img_with_shape = draw_geometry_on_map(
        image=map_img,
        geometry=geometry_rd,
        zoom=zoom,
    )

    # Write the png-formatted image to a bytes stream and encode it using base64
    stream = BytesIO()
    img_with_shape.save(stream, format="png")
    encoded = b64encode(stream.getvalue()).decode()

    return encoded
