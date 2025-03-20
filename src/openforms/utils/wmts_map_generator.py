# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import io
import urllib.request
from math import asinh, modf, pi, radians, tan

from PIL import Image

TILE_SIZE = 256


#  https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._3
class WMTSMapGenerator:
    @staticmethod
    def _deg2num(lat_deg, lon_deg, zoom):
        lat_rad = radians(lat_deg)
        n = 2.0**zoom
        xtile = (lon_deg + 180.0) / 360.0 * n
        ytile = (1.0 - asinh(tan(lat_rad)) / pi) / 2.0 * n
        return xtile, ytile

    @staticmethod
    def deg2num(lat_deg, lon_deg, zoom):
        xtile, ytile = WMTSMapGenerator._deg2num(lat_deg, lon_deg, zoom)
        return int(xtile), int(ytile)

    @staticmethod
    def deg2num_pixel(lat_deg, lon_deg, zoom):
        xtile, ytile = WMTSMapGenerator._deg2num(lat_deg, lon_deg, zoom)
        xpixel = int((xtile % 1) * TILE_SIZE)
        ypixel = int((ytile % 1) * TILE_SIZE)
        return xpixel, ypixel

    @staticmethod
    def calc_tiles_in_pixels(input, pixels):
        # returns the amount of tiles required to span desired number of pixels
        # skip pixels in own tile
        net_pixels = max(0, pixels - input)
        # determine required number of tiles
        fract_part, int_part = modf(net_pixels / TILE_SIZE)
        return int(int_part) if fract_part == 0 else int(int_part + 1)

    @staticmethod
    def load_image(url_template, zoom, x, y, left, top, right, bottom):
        # potential number of tiles left and right, add one for the tile with the marker
        xtiles = left + right + 1
        # same as above but for top, bottom
        ytiles = top + bottom + 1

        print(xtiles, ytiles)

        img = Image.new("RGBA", (xtiles * TILE_SIZE, ytiles * TILE_SIZE), 0)
        try:
            for i in range(-left, right + 1, 1):
                for j in range(-top, bottom + 1, 1):
                    url = url_template.format(z=zoom, x=x + i, y=y + j)
                    print("j", j, url)
                    with urllib.request.urlopen(url) as response:
                        print(response.read())
                        offset = ((i + left) * TILE_SIZE, (j + top) * TILE_SIZE)
                        img.paste(Image.open(io.BytesIO(response.read())), offset)
        except Exception:
            pass  # use empty image in case of errors

        img.show()
        return img

    @staticmethod
    def make_map(url_template, lat, lon, zoom, img_size):
        W, H = img_size
        # x and y tiles
        xt, yt = WMTSMapGenerator.deg2num(lat, lon, zoom)
        # x and y pixel positon within tile
        xp, yp = WMTSMapGenerator.deg2num_pixel(lat, lon, zoom)
        tiles_left = WMTSMapGenerator.calc_tiles_in_pixels(xp, W / 2)
        tiles_top = WMTSMapGenerator.calc_tiles_in_pixels(yp, H / 2)
        tiles_right = WMTSMapGenerator.calc_tiles_in_pixels(TILE_SIZE - xp, W / 2)
        tiles_bottom = WMTSMapGenerator.calc_tiles_in_pixels(TILE_SIZE - yp, H / 2)

        print(tiles_left, tiles_top, tiles_right, tiles_bottom)

        img = WMTSMapGenerator.load_image(
            url_template, zoom, xt, yt, tiles_left, tiles_top, tiles_right, tiles_bottom
        )

        # marker x and y in new map
        mx = int(tiles_left * TILE_SIZE + xp)
        my = int(tiles_top * TILE_SIZE + yp)

        x1 = int(mx - W / 2)
        x2 = x1 + W

        y1 = int(my - H / 2)
        y2 = y1 + H

        # Extract img_size from the larger covering map
        cropped = img.crop((x1, y1, x2, y2))

        return cropped
