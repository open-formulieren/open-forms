# from mpl_toolkits.basemap import Basemap
# import numpy as np
# import datetime
# import matplotlib.pyplot as plt
#
# start_time = datetime.datetime.now()
#
# # projection = ccrs.Projection(
# #         {
# #             "proj": "stere",
# #             "lat_0": 52.15616055555555,
# #             "lon_0": 5.38763888888889,
# #             "k": 0.9999079,
# #             "x_0": 155000,
# #             "y_0": 463000,
# #             "ellps": "bessel",
# #             "units": "m",
# #             "towgs84": "565.2369, 50.0087, 465.658, -0.406857330322398, 0.350732676542563, -1.8703473836068, 4.0812",
# #             "no_defs": True,
# #         }
# #     )
#
# m = Basemap(
#     width=12000000,
#     height=8000000,
#     resolution="c",
#     projection="stere",
#     ellps="bessel",
#     k_0=0.9999079,
#     lat_0=52.15616055555555,
#     lon_0=-5.38763888888889,
# )
# #
# # # setup stereographic basemap.
# # # lat_ts is latitude of true scale.
# # # lon_0,lat_0 is central point.
# # m = Basemap(
# #     width=12000000,
# #     height=8000000,
# #     resolution="l",
# #     projection="stere",
# #     lat_ts=50,
# #     lat_0=50,
# #     lon_0=-107.0,
# # )
# m.drawcoastlines()
#
# m.fillcontinents(color="coral", lake_color="aqua")
# # draw parallels and meridians.
# m.drawparallels(np.arange(-80.0, 81.0, 20.0))
# m.drawmeridians(np.arange(-180.0, 181.0, 20.0))
# m.drawmapboundary(fill_color="aqua")
# # draw tissot's indicatrix to show distortion.
# ax = plt.gca()
# for y in np.linspace(m.ymax / 20, 19 * m.ymax / 20, 9):
#     for x in np.linspace(m.xmax / 20, 19 * m.xmax / 20, 12):
#         lon, lat = m(x, y, inverse=True)
#         poly = m.tissot(lon, lat, 1.5, 100, facecolor="green", zorder=10, alpha=0.5)
#
# plt.title("Stereographic Projection")
# end_time = datetime.datetime.now()
# print(end_time - start_time)
# plt.show()
