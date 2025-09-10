"""
A custom WMTS map generator.

The Amsterdam Signal WMTS generator was used as an inspiration:
https://github.com/Amsterdam/signals/blob/main/app/signals/apps/services/domain/wmts_map_generator.py
"""

from io import BytesIO
from math import ceil, modf

import requests
from PIL import Image
from requests import RequestException
from shapely.geometry import Point

from .constants import ORIGIN_X, ORIGIN_Y, TILE_SIZE
from .utils import px_to_rd


def convert_rd_coordinate_to_tile(
    x_rd: float, y_rd: float, zoom_level: int
) -> tuple[int, int, int, int]:
    """
    Convert a RD coordinate to a tile number and pixel within that tile -
    for x and y.

    :param x_rd: X RD coordinate.
    :param y_rd: Y RD coordinate.
    :param zoom_level: Zoom level.
    :return: Coordinates of the tile with the corresponding pixel inside the tile.
    """
    tile_size_rd = px_to_rd(TILE_SIZE, zoom_level)

    x_remainder, x_quotient = modf((x_rd - ORIGIN_X) / tile_size_rd)
    y_remainder, y_quotient = modf((ORIGIN_Y - y_rd) / tile_size_rd)  # Y-axis reversed

    return (
        int(x_quotient),
        int(x_remainder * TILE_SIZE),
        int(y_quotient),
        int(y_remainder * TILE_SIZE),
    )


def calculate_number_of_tiles(remaining_pixels: int, n_pixels: float) -> int:
    """
    Determine the number of tiles required to fit the pixels.

    :param remaining_pixels: Number of pixels remaining inside the tile - can be in
      any direction.
    :param n_pixels: Number of pixels that need to be fitted.
    :return: Number of tiles required to fit the pixels. 0 means the specified
      number of pixels will fit in the current tile.
    """
    assert 0 <= remaining_pixels <= TILE_SIZE
    assert n_pixels > 0
    # Negative value means there is enough room to fit the pixels, so we set it to 0
    net_pixels = max(0, int(n_pixels - remaining_pixels))
    return ceil(net_pixels / TILE_SIZE)


def construct_image_from_tiles(
    url_template: str,
    zoom_level: int,
    x_tile_center: int,
    y_tile_center: int,
    n_tiles_left: int,
    n_tiles_right: int,
    n_tiles_top: int,
    n_tiles_bottom: int,
) -> Image.Image | None:
    """
    Load tiles with the specified WMTS url template, and construct an image.

    TODO: make asynchronous if we need large images sizes. Note that for images of
     size 400 by 300 px (which is the current size in the map formatter), loading times
     are below 0.5 sec.

    :param url_template: URL template to load tiles from. This URL should be
      formattable x, y, and z parameters. For example:
      https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png
    :param zoom_level: The zoom level to use. Will be set to the z parameter in the
      url template.
    :param x_tile_center: The x coordinate of the center tile.
    :param y_tile_center: The y coordinate of the center tile.
    :param n_tiles_left: The number of tiles to the left of the center tile that
      should be loaded.
    :param n_tiles_right: The number of tiles to the right of the center tile that
      should be loaded.
    :param n_tiles_top: The number of tiles above the center tile that should be
      loaded.
    :param n_tiles_bottom: The number of tiles below the center tile that should be
      loaded.
    :return: The constructed image or ``None`` if (one of) the tiles couldn't be loaded.
    """
    # Total number of tiles in both directions (add 1 for the center tile)
    n_tiles_x = n_tiles_left + n_tiles_right + 1
    n_tiles_y = n_tiles_top + n_tiles_bottom + 1

    # Ranges of tile numbers to load
    tiles_x = range(x_tile_center - n_tiles_left, x_tile_center + n_tiles_right + 1)
    tiles_y = range(y_tile_center - n_tiles_top, y_tile_center + n_tiles_bottom + 1)

    img = Image.new("RGBA", (n_tiles_x * TILE_SIZE, n_tiles_y * TILE_SIZE), 0)
    for i, tile_x in enumerate(tiles_x):
        for j, tile_y in enumerate(tiles_y):
            url = url_template.format(z=zoom_level, x=tile_x, y=tile_y)
            try:
                res = requests.get(url)
                res.raise_for_status()
            except RequestException:
                return None

            # The location of where the upper left corner of the tile image should
            # be pasted on the total image.
            offset = (i * TILE_SIZE, j * TILE_SIZE)
            img.paste(Image.open(BytesIO(res.content)), offset)

    return img


def generate_map_image(
    url_template: str,
    center: Point,
    zoom: int,
    img_size: tuple[int, int],
) -> Image.Image | None:
    """
    Generate a WMTS map image from a URL template.

    :param url_template: URL template to load tiles from. This URL should be
      formattable x, y, and z parameters. For example:
      https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png
    :param center: The center of the image, should be in RD coordinates.
    :param zoom: The desired zoom level.
    :param img_size: The desired image size in pixels (width, height).
    :return: WMTS map image or ``None`` if the image could not be constructed.
    """
    x_rd, y_rd = center.coords[0]

    # Determine on which tile coordinate the center point lies
    res = convert_rd_coordinate_to_tile(x_rd, y_rd, zoom)
    x_tile_number, x_tile_pixel, y_tile_number, y_tile_pixel = res

    w, h = img_size
    # Determine how many tiles we need w.r.t. the center tile in all directions, to
    # fit the specified image size.
    n_tiles_left = calculate_number_of_tiles(x_tile_pixel, w / 2)
    n_tiles_right = calculate_number_of_tiles(TILE_SIZE - x_tile_pixel, w / 2)
    n_tiles_top = calculate_number_of_tiles(y_tile_pixel, h / 2)
    n_tiles_bottom = calculate_number_of_tiles(TILE_SIZE - y_tile_pixel, h / 2)

    # Create a map image for the specified tiles
    full_img = construct_image_from_tiles(
        url_template,
        zoom,
        x_tile_number,
        y_tile_number,
        n_tiles_left,
        n_tiles_right,
        n_tiles_top,
        n_tiles_bottom,
    )

    if full_img is None:
        return None

    # The center of our desired image - essentially it is `center` converted to
    # pixel coordinates.
    x_center_px = n_tiles_left * TILE_SIZE + x_tile_pixel
    y_center_px = n_tiles_top * TILE_SIZE + y_tile_pixel

    # Upper left corner
    x_1 = x_center_px - w // 2
    y_1 = y_center_px - h // 2
    # Lower right corner
    x_2 = x_1 + w
    y_2 = y_1 + h

    # The size of the image we created will be a multiple of the tile size, so we
    # need to crop it to match our specified image size.
    return full_img.crop((x_1, y_1, x_2, y_2))
