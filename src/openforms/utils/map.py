from openforms.api.geojson import PointGeometry, LineStringGeometry, PolygonGeometry, GeoJsonGeometryTypes

import base64
import datetime
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, PathPatch
from matplotlib.path import Path

import cartopy.crs as ccrs


# @TODO remove
# from mpl_toolkits.basemap import Basemap
# import numpy as np


type MapGeometry = PointGeometry | LineStringGeometry | PolygonGeometry


def generate_cartopy_map(
    geometry: MapGeometry, tileLayerIdentifier: str | None = None
) -> str:
    start_time = datetime.datetime.now()
    # We don't require interactions with this map, so lets limit matplotlib to static use
    matplotlib.use('AGG')

    # Copied from https://github.com/arbakker/pdok-js-map-examples/blob/c9ee1c/leaflet-geojson-wmts-epsg28992/index.js
    projection = ccrs.Projection(
        {
            "proj": "stere",
            "lat_0": 52.15616055555555,
            "lon_0": 5.38763888888889,
            "k": 0.9999079,
            "x_0": 155000,
            "y_0": 463000,
            "ellps": "bessel",
            "units": "m",
            "towgs84": "565.2369, 50.0087, 465.658, -0.406857330322398, 0.350732676542563, -1.8703473836068, 4.0812",
            "no_defs": True,
        }
    )

    # @TODO check if bounds and comment are correct
    # Projection bounds left, right, top, bottom
    projection.bounds = (
        -285401.92,
        595401.92,
        22598.08,
        903401.92,
    )

    # Make map with projection
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, projection=projection)

    ax.set_xlim(-285401.92, 595401.92)
    ax.set_ylim(22598.08, 903401.92)

    # Add shapes
    match geometry:
        case {"type": GeoJsonGeometryTypes.point, "coordinates": list() as coordinates}:
            marker_x, marker_y = coordinates
            print(marker_x, marker_y)
            plat = ax.plot(marker_x, marker_y, "ro", markersize=7, transform=ccrs.Geodetic())
            print(plat[0].get_bbox(), ax.get_position())

            # @TODO the transform is only done on the plot, instead of on the marker x and y. `set_extent` currently results in slightly wrong focus
            ax.set_extent([marker_x - 0.002, marker_x + 0.002, marker_y - 0.002, marker_y + 0.002])

        case {"type": GeoJsonGeometryTypes.line_string, "coordinates": list() as coordinates}:
            pass

        case {"type": GeoJsonGeometryTypes.polygon, "coordinates": list() as coordinates}:
            geo_bro = ccrs.Geodetic()

            polygon_data = [
              [
                5.481597,
                52.214099
              ],
              [
                5.144865,
                52.225485
              ],
              [
                4.976882,
                52.1825
              ],
              [
                4.879305,
                52.053588
              ],
              [
                5.149163,
                52.009988
              ],
              [
                5.512504,
                52.01596
              ],
              [
                5.728955,
                52.056119
              ],
              [
                5.481597,
                52.214099
              ]
            ]

            # path = Path(coordinates)
            # path = Path(polygon_data[0])
            polygon = Polygon(polygon_data, closed=True, transform=ccrs.Geodetic())
            print(polygon)
            ax.add_patch(polygon)
            print("aadded the patch")

            # [5.292019, 52.132987], [5.290362, 52.133197], [5.290123, 52.132872], [5.290087, 52.132509], [5.291351, 52.132318], [5.292394, 52.132534], [5.292019, 52.132987]
            # marker_x = [5.292019, 5.290362, 5.290123, 5.290087, 5.291351, 5.292394, 5.292019]
            # marker_y = [52.132987, 52.133197, 52.132872, 52.132509, 52.132318, 52.132534, 52.132987]
            # print(coordinates)

            # marker_x, marker_y = coordinates
            # print(marker_x, marker_y)
            # ax.plot(marker_x, marker_y, "ro", gapcolor="r", markersize=2, linestyle='-', transform=ccrs.Geodetic())
            #
            # # @TODO the transform is only done on the plot, instead of on the marker x and y. `set_extent` currently results in slightly wrong focus
            # ax.set_extent([marker_x - 0.002, marker_x + 0.002, marker_y - 0.002, marker_y + 0.002])

    # @TODO set dynamic with tileLayerIdentifier
    ax.add_wmts(
        wmts="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0",
        layer_name="standaard",
    )

    # @TODO attribution
    # text = AnchoredText('Kaartgegevens &copy Kadaster | Verbeter de kaart',
    #                     loc=4, prop={'size': 12}, frameon=True)
    # ax.add_artist(text)

    # Render map to temporary file and return it utf-8 encoded
    tmpfile = BytesIO()
    fig.savefig(tmpfile, bbox_inches="tight", format="png")
    encoded = base64.b64encode(tmpfile.getvalue()).decode("utf-8")

    end_time = datetime.datetime.now()
    print(end_time-start_time)

    return encoded


# @TODO remove
# def generate_basemap_map(geometry: MapGeometry, tileLayerIdentifier: str | None = None) -> str:
#     start_time = datetime.datetime.now()
#     matplotlib.use('AGG')
#
#     m = Basemap(
#         width=12000000,
#         height=8000000,
#         resolution="c",
#         projection="stere",
#         ellps="bessel",
#         k_0=0.9999079,
#         lat_0=52.15616055555555,
#         lon_0=-5.38763888888889,
#     )
#
#     m.drawcoastlines()
#     m.drawcountries()
#     m.drawstates()
#
#     m.fillcontinents(color="coral", lake_color="aqua")
#     # draw parallels and meridians.
#     m.drawparallels(np.arange(-80.0, 81.0, 20.0))
#     m.drawmeridians(np.arange(-180.0, 181.0, 20.0))
#     m.drawmapboundary(fill_color="aqua")
#     # draw tissot's indicatrix to show distortion.
#     ax = plt.gca()
#     for y in np.linspace(m.ymax / 20, 19 * m.ymax / 20, 9):
#         for x in np.linspace(m.xmax / 20, 19 * m.xmax / 20, 12):
#             lon, lat = m(x, y, inverse=True)
#             poly = m.tissot(lon, lat, 1.5, 100, facecolor="green", zorder=10, alpha=0.5)
#
#     tmpfile = BytesIO()
#     plt.savefig(tmpfile, bbox_inches="tight", format="png")
#     encoded = base64.b64encode(tmpfile.getvalue()).decode("utf-8")
#
#     end_time = datetime.datetime.now()
#     print(end_time - start_time)
#
#     return encoded
