import io
import requests
from math import ceil

from PIL import Image
from pyproj import Transformer
from requests import RequestException
from shapely.geometry import Point

# Constant values are from https://api.pdok.nl/lv/bgt/ogc/v1/tileMatrixSets/NetherlandsRDNewQuad
TILE_SIZE = 256
transformer = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)

# PDOK origin of map
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


"""
A custom WMTS map generator based on the Amsterdam Signal setup.

This generator used the Signal WMTS map generator as inspiration:
https://github.com/Amsterdam/signals/blob/main/app/signals/apps/services/domain/wmts_map_generator.py
"""

def px_to_rd(value: int, zoom_level: int) -> float:
    res = RESOLUTIONS[zoom_level]
    return value * res

class WMTSMapGenerator:
    @staticmethod
    def convert_rd_coordinate_to_tile(
        x_rd: float, y_rd: float, zoom_level: int
    ) -> tuple[int, int]:
        """
        Convert a RD coordinate to a tile number.

        :param x_rd: X RD coordinate.
        :param y_rd: Y RD coordinate.
        :param zoom_level: Zoom level.
        :return: Coordinates of the tile.
        """
        tile_size_rd = px_to_rd(TILE_SIZE, zoom_level)
        x_tile = int((x_rd - ORIGIN_X) / tile_size_rd)
        y_tile = int((ORIGIN_Y - y_rd) / tile_size_rd)  # Y-axis reversed
        return x_tile, y_tile

    @staticmethod
    def convert_rd_coordinate_to_pixel_in_tile(
        x_rd: float, y_rd: float, zoom_level: int
    ) -> tuple[int, int]:
        """
        Convert a RD coordinate to a pixel coordinate inside a tile.

        :param x_rd: X RD coordinate.
        :param y_rd: Y RD coordinate.
        :param zoom_level: Zoom level.
        :return: Pixel coordinates inside the tile.
        """
        tile_size_rd = px_to_rd(TILE_SIZE, zoom_level)
        x_tile_float = (x_rd - ORIGIN_X) / tile_size_rd
        y_tile_float = (ORIGIN_Y - y_rd) / tile_size_rd
        x_pixel = int((x_tile_float % 1) * TILE_SIZE)
        y_pixel = int((y_tile_float % 1) * TILE_SIZE)
        return x_pixel, y_pixel

    @staticmethod
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

    # TODO-4951: this should probably be asynchronous
    @staticmethod
    def load_image(
        url_template: str,
        zoom_level: int,
        x: int,
        y: int,
        left: int,
        right: int,
        top: int,
        bottom: int,
    ) -> Image:
        """

        :param url_template:
        :param zoom_level:
        :param x:
        :param y:
        :param left:
        :param right:
        :param top:
        :param bottom:
        :return:
        """
        # Total number of tiles in both directions (add 1 for the center tile)
        n_tiles_x = left + right + 1
        n_tiles_y = top + bottom + 1
        img = Image.new("RGBA", (n_tiles_x * TILE_SIZE, n_tiles_y * TILE_SIZE), 0)

        for i in range(-left, right + 1):
            for j in range(-top, bottom + 1):
                tile_x = x + i
                tile_y = y + j
                url = url_template.format(z=zoom_level, x=tile_x, y=tile_y)
                try:
                    res = requests.get(url)
                    res.raise_for_status()
                except RequestException:
                    continue  # Leave transparent if tile load fails

                # The location of where the upper left corner of the image
                # should be pasted
                offset = ((i + left) * TILE_SIZE, (j + top) * TILE_SIZE)
                img.paste(Image.open(io.BytesIO(res.content)), offset)

        return img

    @classmethod
    def make_map_rd(
        cls,
        url_template: str,
        center: Point,
        zoom: int,
        img_size: tuple[int, int],
    ) -> Image:
        x_rd, y_rd = center.coords[0]

        # Determine on which tile 'coordinate' the center point lies
        center_tile_x, center_tile_y = cls.convert_rd_coordinate_to_tile(x_rd, y_rd, zoom)
        # Inside this tile, determine on which pixels the center point lies
        x_pixel, y_pixel = cls.convert_rd_coordinate_to_pixel_in_tile(x_rd, y_rd, zoom)

        w, h = img_size
        # Determine how many tiles we need w.r.t. the center tile in all directions, to
        # fit the specified image size.
        n_tiles_to_the_left = cls.calculate_number_of_tiles(x_pixel, w / 2)
        n_tiles_to_the_right = cls.calculate_number_of_tiles(TILE_SIZE - x_pixel, w / 2)
        n_tiles_above = cls.calculate_number_of_tiles(y_pixel, h / 2)
        n_tiles_below = cls.calculate_number_of_tiles(TILE_SIZE - y_pixel, h / 2)

        full_img = cls.load_image(
            url_template,
            zoom,
            center_tile_x,
            center_tile_y,
            n_tiles_to_the_left,
            n_tiles_to_the_right,
            n_tiles_above,
            n_tiles_below
        )
        full_img.show()

        mx = n_tiles_to_the_left * TILE_SIZE + x_pixel
        my = n_tiles_above * TILE_SIZE + y_pixel

        x1 = mx - w // 2
        y1 = my - h // 2
        x2 = x1 + w
        y2 = y1 + h

        # Crop image to centralize on the x_rd and y_rd
        cropped_img = full_img.crop((x1, y1, x2, y2))
        cropped_img.show()

        return cropped_img
