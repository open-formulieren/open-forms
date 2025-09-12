from typing import assert_never

from PIL import Image, ImageDraw
from shapely import transform
from shapely.geometry.base import BaseGeometry

from .constants import ZOOM_LEVEL_TO_RESOLUTION

SHAPE_COLOUR = "#3388ff"  # Same as the shape in the frontend
POLYGON_FILL_ALPHA = "32"  # 50% in hex
LINE_WIDTH = 3


def convert_geometry_rd_to_pixels(
    geometry_rd: BaseGeometry, zoom: int, image_size: tuple[int, int]
) -> BaseGeometry:
    """
    Convert a geometry shape in RD coordinates to pixel coordinates, by:

     1. calculating the distance from each coordinate to the center of the shape;
     2. converting it to a distance in pixels with the resolution corresponding to the
        specified zoom level;
     3. adding this pixel distance to the coordinates of the center of the image.

    :param geometry_rd: Shape to convert in RD coordinates.
    :param zoom: Zoom level.
    :param image_size: Image size in pixels.
    :return: Shape in pixel coordinates.
    """
    geom_center_x, geom_center_y = geometry_rd.centroid.coords[0]

    w, h = image_size
    res = ZOOM_LEVEL_TO_RESOLUTION[zoom]

    def project_rd_to_pixel(x: float, y: float) -> tuple[float, float]:
        dx = (x - geom_center_x) / res
        dy = (geom_center_y - y) / res  # Y-axis reversed
        return w / 2 + dx, h / 2 + dy

    return transform(
        geometry_rd, project_rd_to_pixel, include_z=False, interleaved=False
    )


def draw_geometry_on_map(
    image: Image.Image, geometry: BaseGeometry, zoom: int, upscaling_factor: int = 4
) -> Image.Image:
    """
    Draw a geometry shape in RD coordinates on a map image.

    An upscaling factor can be passed to enlarge the image before drawing the shape.
    This helps with antialiasing of the shape, as it might look very pixilated
    depending on the image size. After drawing, the image is downscaled again to the
    original size. Note that this means we do not draw on the original image, but on a
    copy.

    :param image: The map image to draw on.
    :param geometry: The geometry shape in RD coordinates.
    :param zoom: The desired zoom level.
    :param upscaling_factor: The upscaling factor with which the image size will be
      increased, and the (transformed) coordinates will be multiplied.
    :return: The map image with the geometry shape.
    """
    assert upscaling_factor >= 1
    geometry_px = convert_geometry_rd_to_pixels(geometry, zoom, image.size)

    # Perform upscaling
    original_size = image.size
    if upscaling_factor != 1:
        new_size = (image.size[0] * upscaling_factor, image.size[1] * upscaling_factor)
        image = image.resize(new_size)
        geometry_px = transform(
            geometry_px,
            lambda x, y: (x * upscaling_factor, y * upscaling_factor),
            include_z=False,
            interleaved=False,
        )

    match geometry_px.geom_type:
        case "Point":
            radius = LINE_WIDTH * upscaling_factor
            x, y = geometry_px.coords[0]
            draw = ImageDraw.Draw(image)
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=SHAPE_COLOUR,
                outline="black",
            )
        case "LineString":
            draw = ImageDraw.Draw(image)
            draw.line(
                list(geometry_px.coords),
                fill=SHAPE_COLOUR,
                width=LINE_WIDTH * upscaling_factor,
            )
        case "Polygon":
            overlay = Image.new("RGBA", image.size)
            draw = ImageDraw.Draw(overlay)
            draw.polygon(
                list(geometry_px.exterior.coords),
                outline=SHAPE_COLOUR,
                width=LINE_WIDTH * upscaling_factor,
                fill=f"{SHAPE_COLOUR}{POLYGON_FILL_ALPHA}",
            )
            image = Image.alpha_composite(image, overlay)
        case _:  # pragma: no cover
            assert_never(geometry_px.geom_type)

    return image.resize(original_size, Image.Resampling.HAMMING)
