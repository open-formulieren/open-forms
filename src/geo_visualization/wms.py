"""
Client code for WebMapService interaction (tile overlays).
"""

from collections.abc import Collection
from typing import Literal, assert_never, cast
from urllib.parse import urlparse, urlunparse

from django.core.cache import cache

import requests
import structlog
from lxml import etree

from .typing import SupportedCrs

__all__ = ["get_map", "VersionError"]

logger = structlog.stdlib.get_logger(__name__)

type SupportedVersion = Literal["1.1.1", "1.3.0"]

SUPPORTED_VERSIONS: Collection[SupportedVersion] = (
    "1.1.1",
    "1.3.0",
)


class VersionError(Exception):
    pass


def _check_wms_version(session: requests.Session, url: str) -> SupportedVersion:
    # validate the URL/version from the capabilities
    capabilities_response = session.get(
        url,
        params={"service": "WMS", "request": "GetCapabilities"},
    )
    try:
        capabilities_response.raise_for_status()
        capabilities_root = etree.fromstring(capabilities_response.content)
    except (requests.RequestException, etree.XMLSyntaxError) as exc:
        logger.warning("wms_version_extraction_failure", exc_info=exc)
        raise VersionError("Could not determine WMS version") from exc

    version = capabilities_root.attrib["version"]
    if version not in SUPPORTED_VERSIONS:
        raise VersionError(f"Version '{version}' is not supported.")
    return cast(SupportedVersion, version)


def get_map(
    url: str,
    *,
    crs: SupportedCrs,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
    layers: Collection[str],
) -> bytes | None:
    """
    Get a WMS map image as binary content.

    :param url: The WMS service URL, fully qualified.
    :param layers: Layers to draw.
    :param crs: Coordinate reference system of the bounding box.
    :param bbox: Bounding box coordinates of the image to generate.
      Order: min_x, min_y, max_x, max_y.
    :param width: Width of the image in pixels.
    :param height: Height of the image in pixels.
    :param image_format: Format of the image, e.g. 'image/png'.
    :param transparent: Whether to render the image with a transparent background.
    :return: bytestring of the map image. ``None`` if the image could not be loaded.
    """
    url = urlunparse(urlparse(url)._replace(query=""))

    with (
        structlog.contextvars.bound_contextvars(service_url=url),
        requests.Session() as session,
    ):
        logger.debug("get_wms_map_image_start", layers=layers)
        version = cache.get_or_set(
            f"wms_version|{url}",
            default=lambda: _check_wms_version(session, url),
            timeout=60 * 60 * 12,  # 12 hours
        )
        assert version is not None

        crs_key: str
        match version:
            case "1.3.0":
                crs_key = "crs"
            case "1.1.1":
                crs_key = "srs"
            case _:  # pragma: no cover
                assert_never(version)

        # request the actual image
        response = session.get(
            url,
            params={
                "service": "WMS",
                "request": "GetMap",
                crs_key: crs,
                "layers": ",".join(layers),
                "styles": "",
                "format": "image/png",
                "transparent": True,
                "version": version,
                "bbox": ",".join(map(str, bbox)),
                "width": width,
                "height": height,
            },
        )

        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("wms_request_failed", exc_info=exc)
            return

        # if we get back an image, return the content, otherwise process errors
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("image/"):
            return response.content

        # otherwise we expect errors
        assert content_type == "" or content_type.startswith("text/xml")

        root = etree.fromstring(response.content)
        error: etree._Element | None
        match version:
            case "1.3.0":
                error = root.find(
                    "ogc:ServiceException",
                    namespaces={"ogc": "http://www.opengis.net/ogc"},
                )
            case "1.1.1":
                error = root.find("ServiceException")
            case _:  # pragma: no cover
                assert_never(version)

        if error is not None:
            logger.warning(
                "wms_request_invalid",
                message=(error.text or "").strip(),
                code=error.get("code"),
                locator=error.get("locator"),
            )
