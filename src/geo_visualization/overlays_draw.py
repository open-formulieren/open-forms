from collections.abc import Collection
from io import BytesIO
from typing import assert_never

import structlog
from PIL import Image, UnidentifiedImageError
from shapely import Point

from .constants import ZOOM_LEVEL_TO_RESOLUTION
from .typing import Overlay
from .wms import get_map

logger = structlog.stdlib.get_logger(__name__)


def draw_wms_layers_on_map(
    image: Image.Image, url: str, layers: Collection[str], center_rd: Point, zoom: int
) -> None:
    """
    Draw WMS layers on a map image.

    :param image: Map image.
    :param url: Url of the WMS. Query parameters present in the url will be stripped.
    :param layers: Layers of the WMS to draw.
    :param center_rd: Center of the map in RD coordinates.
    :param zoom: Zoom level.
    """
    # Convert the bounding box of the image to RD coordinates
    geom_center_x_rd, geom_center_y_rd = center_rd.coords[0]
    res = ZOOM_LEVEL_TO_RESOLUTION[zoom]
    w, h = image.size

    def project_pixel_to_rd(x_px: int, y_px: int):
        x_rd = (x_px - w / 2) * res + geom_center_x_rd
        y_rd = (h / 2 - y_px) * res + geom_center_y_rd  # Y-axis reversed
        return x_rd, y_rd

    min_x, max_y = project_pixel_to_rd(0, 0)
    max_x, min_y = project_pixel_to_rd(w, h)

    wms_img_data = get_map(
        url=url,
        crs="EPSG:28992",
        bbox=(min_x, min_y, max_x, max_y),
        width=w,
        height=h,
        layers=layers,
    )
    if wms_img_data is None:
        logger.warning("get_wms_map_image_failed", reason="no image data returned")
        return

    try:
        wms_img = Image.open(BytesIO(wms_img_data))
    except UnidentifiedImageError as exc:
        logger.warning(
            "get_wms_map_image_failed",
            reason="unusable image data returned",
            exc_info=exc,
        )
        return
    else:
        image.alpha_composite(wms_img)


def draw_overlays_on_map(
    image: Image.Image, overlays: Collection[Overlay], center_rd: Point, zoom: int
) -> None:
    """
    Draw overlays on a map image.

    :param image: Map image .
    :param overlays: Overlays to draw.
    :param center_rd: The center of the map in RD coordinates.
    :param zoom: Zoom level.
    """
    for overlay in overlays:
        match overlay["type"]:
            case "wms":
                draw_wms_layers_on_map(
                    image=image,
                    url=overlay["url"],
                    layers=overlay["layers"],
                    center_rd=center_rd,
                    zoom=zoom,
                )
            case "wfs":  # pragma: no cover
                raise NotImplementedError()
            case _:  # pragma: no cover
                assert_never(overlay["type"])
