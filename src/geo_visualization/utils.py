from pyproj import Transformer
from shapely import transform as shapely_transform
from shapely.geometry.base import BaseGeometry

from .constants import ZOOM_LEVEL_TO_RESOLUTION


def px_to_rd(value: int, zoom_level: int) -> float:
    """Convert a pixel vector, e.g. width or height, to an RD vector."""
    assert min(ZOOM_LEVEL_TO_RESOLUTION) <= zoom_level <= max(ZOOM_LEVEL_TO_RESOLUTION)

    res = ZOOM_LEVEL_TO_RESOLUTION[zoom_level]
    return value * res


def geojson_to_rd(geometry: BaseGeometry) -> BaseGeometry:
    """Convert a geojson coordinates system to a RD (Rijksdriehoek) coordinates system.
    (EPSG:4326 to EPSG:28992)
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)
    return shapely_transform(
        geometry,
        transformer.transform,  # type: ignore
        include_z=False,
        interleaved=False,
    )


def find_maximum_zoom(
    geometry_rd: BaseGeometry,
    image_size: tuple[int, int],
    max_zoom: int = max(ZOOM_LEVEL_TO_RESOLUTION),
    min_zoom: int = min(ZOOM_LEVEL_TO_RESOLUTION),
    padding: float = 1.2,
) -> int:
    """
    Find the maximum zoom level for which the geometry shape fits within the specified
    image size.

    :param geometry_rd: The shape that should be drawn on the map in RD coordinates.
    :param image_size: The desired image size in pixels (width, height).
    :param max_zoom: The maximum zoom level.
    :param min_zoom: The minimum zoom level.
    :param padding: Multiplier for the geometry shape - can be used to (artificially)
      enlarge the shape to ensure there is some margin near the edges.
    :return: Best zoom level.
    """
    min_x, min_y, max_x, max_y = geometry_rd.bounds
    geometry_w_rd = (max_x - min_x) * padding
    geometry_h_rd = (max_y - min_y) * padding
    img_w_px, img_h_px = image_size

    # Start at max zoom, because the shape is generally not large
    for zoom in range(max_zoom, min_zoom - 1, -1):
        # Convert image size to RD coordinates
        img_w_rd = px_to_rd(img_w_px, zoom)
        img_h_rd = px_to_rd(img_h_px, zoom)
        # Return the zoom level if the size of the image is larger than the size of the
        # shape we are trying to draw (in RD coordinates).
        if img_w_rd >= geometry_w_rd and img_h_rd >= geometry_h_rd:
            return zoom

    return min_zoom  # fallback
