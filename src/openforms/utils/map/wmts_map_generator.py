import io
import urllib.request
from math import modf

from PIL import Image
from pyproj import Transformer

# Constant values are from https://api.pdok.nl/lv/bgt/ogc/v1/tileMatrixSets/NetherlandsRDNewQuad
TILE_SIZE = 256
transformer = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)

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


"""
A custom WMTS map generator based on the Amsterdam Signal setup.

This generator used the Signal WMTS map generator as inspiration:
https://github.com/Amsterdam/signals/blob/main/app/signals/apps/services/domain/wmts_map_generator.py
"""


class WMTSMapGenerator:
    @staticmethod
    def rd_to_tile(x_rd: float, y_rd: float, zoom_level: int) -> tuple[int, int]:
        res = RESOLUTIONS[zoom_level]
        xtile = int((x_rd - ORIGIN_X) / (TILE_SIZE * res))
        ytile = int((ORIGIN_Y - y_rd) / (TILE_SIZE * res))
        return xtile, ytile

    @staticmethod
    def rd_to_pixel_in_tile(
        x_rd: float, y_rd: float, zoom_level: int
    ) -> tuple[int, int]:
        res = RESOLUTIONS[zoom_level]
        xtile_float = (x_rd - ORIGIN_X) / (TILE_SIZE * res)
        ytile_float = (ORIGIN_Y - y_rd) / (TILE_SIZE * res)
        xpixel = int((xtile_float % 1) * TILE_SIZE)
        ypixel = int((ytile_float % 1) * TILE_SIZE)
        return xpixel, ypixel

    @staticmethod
    def calc_tiles_in_pixels(input_px: int, pixels: float) -> int:
        net_pixels = max(0, int(pixels - input_px))
        fract_part, int_part = modf(net_pixels / TILE_SIZE)
        return int(int_part) if fract_part == 0 else int(int_part + 1)

    @staticmethod
    def load_image(
        url_template: str,
        zoom_level: int,
        x: int,
        y: int,
        left: int,
        top: int,
        right: int,
        bottom: int,
    ) -> Image:
        xtiles = left + right + 1
        ytiles = top + bottom + 1
        img = Image.new("RGBA", (xtiles * TILE_SIZE, ytiles * TILE_SIZE), 0)

        for i in range(-left, right + 1):
            for j in range(-top, bottom + 1):
                tile_x = x + i
                tile_y = y + j
                url = url_template.format(z=zoom_level, x=tile_x, y=tile_y)
                try:
                    with urllib.request.urlopen(url) as response:
                        offset = ((i + left) * TILE_SIZE, (j + top) * TILE_SIZE)
                        img.paste(Image.open(io.BytesIO(response.read())), offset)
                except Exception:
                    pass  # Leave transparent if tile load fails

        return img

    @classmethod
    def make_map_rd(
        this,
        url_template: str,
        x_rd: float,
        y_rd: float,
        zoom: int,
        img_size: tuple[int, int],
    ) -> Image:
        W, H = img_size
        xt, yt = this.rd_to_tile(x_rd, y_rd, zoom)
        xp, yp = this.rd_to_pixel_in_tile(x_rd, y_rd, zoom)

        tiles_left = this.calc_tiles_in_pixels(xp, W / 2)
        tiles_top = this.calc_tiles_in_pixels(yp, H / 2)
        tiles_right = this.calc_tiles_in_pixels(TILE_SIZE - xp, W / 2)
        tiles_bottom = this.calc_tiles_in_pixels(TILE_SIZE - yp, H / 2)

        full_img = this.load_image(
            url_template, zoom, xt, yt, tiles_left, tiles_top, tiles_right, tiles_bottom
        )

        mx = tiles_left * TILE_SIZE + xp
        my = tiles_top * TILE_SIZE + yp

        x1 = mx - W // 2
        y1 = my - H // 2
        x2 = x1 + W
        y2 = y1 + H

        # Crop image to centralize on the x_rd and y_rd
        return full_img.crop((x1, y1, x2, y2))
