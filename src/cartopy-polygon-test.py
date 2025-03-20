# import matplotlib.pyplot as plt
# import numpy as np
#
# from matplotlib.backend_bases import MouseButton
# from matplotlib.patches import PathPatch, Polygon
# from matplotlib.path import Path
#
# import cartopy.crs as ccrs
#
# projection = ccrs.Projection(
#     {
#         "proj": "stere",
#         "lat_0": 52.15616055555555,
#         "lon_0": 5.38763888888889,
#         "k": 0.9999079,
#         "x_0": 155000,
#         "y_0": 463000,
#         "ellps": "bessel",
#         "units": "m",
#         "towgs84": "565.2369, 50.0087, 465.658, -0.406857330322398, 0.350732676542563, -1.8703473836068, 4.0812",
#         "no_defs": True,
#     }
# )
#
# # @TODO check if bounds and comment are correct
# # Projection bounds left, right, top, bottom
# projection.bounds = (
#     5.29,
#     5.294,
#     52.134,
#     52.132,
#     # -285401.92,
#     # 595401.92,
#     # 22598.08,
#     # 903401.92,
# )
#
#
# fig = plt.figure(figsize=(4, 4))
# ax = fig.add_subplot(111, projection=projection)
# # fig, ax = plt.subplots()
#
# polygon_data = [
#     [
#         [5.292019, 52.132987],
#         [5.290362, 52.133197],
#         [5.290123, 52.132872],
#         [5.290087, 52.132509],
#         [5.291351, 52.132318],
#         [5.292394, 52.132534],
#         [5.292019, 52.132987],
#     ]
# ]
#
# # path = Path(coordinates)
# # path = Path(polygon_data[0])
# polygon = Polygon(polygon_data[0], color="r", closed=True)
# print(polygon)
# ax.add_patch(polygon)
# print("aadded the patch")
#
# # pathdata = [
# #     (Path.MOVETO, (1.58, -2.57)),
# #     (Path.CURVE4, (0.35, -1.1)),
# #     (Path.CURVE4, (-1.75, 2.0)),
# #     (Path.CURVE4, (0.375, 2.0)),
# #     (Path.LINETO, (0.85, 1.15)),
# #     (Path.CURVE4, (2.2, 3.2)),
# #     (Path.CURVE4, (3, 0.05)),
# #     (Path.CURVE4, (2.0, -0.5)),
# #     (Path.CLOSEPOLY, (1.58, -2.57)),
# # ]
# #
# # codes, verts = zip(*pathdata)
# # path = Path(verts, codes)
# # patch = PathPatch(path, facecolor="green", edgecolor="yellow", alpha=0.5)
# # ax.add_patch(patch)
#
# ax.set_title("drag vertices to update path")
# # 5.29,
# #     5.294,
# #     52.134,
# #     52.132,
# ax.set_xlim(5.29, 5.294)
# ax.set_ylim(52.134, 52.132)
#
# plt.show()
