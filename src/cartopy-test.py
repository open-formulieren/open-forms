# import matplotlib.pyplot as plt
# from matplotlib.patches import Polygon, PathPatch
#
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
#
# projection = ccrs.Projection(
#     {
#         "proj": "sterea",
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
# print(projection)
# projection.bounds = (
#     -285401.92,
#     595401.92,
#     22598.08,
#     903401.92,
# )
#
# # Make map and set view to the Netherlands
# fig = plt.figure(figsize=(10, 10))
# ax = fig.add_subplot(111, projection=projection)
# # ax.set_extent([2.92, 7.92, 50.38, 54.42])
#
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
# polygon = Polygon(polygon_data[0], transform=ccrs.Geodetic())
# print(polygon)
# ax.add_patch(polygon)
# print("after add_patch")
#
#
# # Add marker
# # marker_x = 4.939886
# # marker_y = 52.511807
# # ax.plot(marker_x, marker_y, "bo", markersize=7, transform=ccrs.Geodetic())
# # @TODO the transform is only done on the plot. `set_extent` results in slightly wrong focus
# # ax.set_extent([marker_x - 0.002, marker_x + 0.002, marker_y - 0.002, marker_y + 0.002])
#
# # ax.coastlines()
# # ax.stock_img()
#
# # ax.add_wmts(
# #     wmts="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0",
# #     layer_name="standaard",
# # )
#
# # ax.add_feature(cfeature.LAND)
# # ax.add_feature(cfeature.STATES, linestyle=":")
# # ax.add_feature(cfeature.OCEAN)
# # ax.add_feature(cfeature.COASTLINE)
# # ax.add_feature(cfeature.BORDERS, linestyle=":")
# # ax.add_feature(cfeature.LAKES, alpha=0.5)
# # ax.add_feature(cfeature.RIVERS)
#
# plt.show()
# # plt.savefig("cartopy_map.png", bbox_inches="tight")
