import logging
from dataclasses import dataclass

from django.contrib.gis.geos import fromstr

import requests
from ape_pie import APIClient

logger = logging.getLogger(__name__)


# API DATA MODELS


@dataclass
class RD:
    x: float
    y: float

    @classmethod
    def fromtuple(cls, value: tuple[float, float]):
        x, y = value
        return cls(x=x, y=y)


@dataclass
class LatLng:
    lat: float
    lng: float

    @classmethod
    def fromtuple(cls, value: tuple[float, float]):
        lng, lat = value
        return cls(lat=lat, lng=lng)


@dataclass
class Location:
    label: str
    lat_lng: LatLng
    rd: RD | None


def _parse_coordinates(doc: dict, key: str) -> tuple[float, float] | None:
    if not (wkt_value := doc.get(key)):
        return None
    try:
        # we expect a two-tuple, and not any arbitrary shape
        coord0, coord1 = fromstr(wkt_value)
    except (ValueError, TypeError):
        logger.info("Malformed %s in location server response: %r", key, doc)
        return None
    return coord0, coord1


def _process_search_result(doc: dict) -> Location | None:
    label = doc.get("weergavenaam", "")
    lat_lng = _parse_coordinates(doc, "centroide_ll")
    x_y = _parse_coordinates(doc, "centroide_rd")
    if not lat_lng:
        return None
    return Location(
        label=label,
        lat_lng=LatLng.fromtuple(lat_lng),
        # TODO: calculate rd when missing from lat_lng
        rd=RD.fromtuple(x_y) if x_y is not None else None,
    )


# CLIENT IMPLEMENTATIONS


class LocatieServerClient(APIClient):
    """
    Client for the Kadaster locatieserver API.

    Documentation: https://api.pdok.nl/bzk/locatieserver/search/v3_1/ui/
    """

    def free_address_search(
        self, query: str, reraise_errors: bool = False
    ) -> list[Location]:
        """
        Find addresses for a given input query.
        """
        try:
            response = self.get("v3_1/free", params={"q": query})
            response.raise_for_status()
        except requests.RequestException as exc:
            if reraise_errors:
                raise exc
            logger.exception("Couldn't retrieve pdok locatieserver data", exc_info=exc)
            return []

        docs: list[dict] = response.json().get("response", {}).get("docs")
        if docs is None:
            # no response with docs: return empty
            return []

        locations = [
            location for doc in docs if (location := _process_search_result(doc))
        ]
        return locations

    def reverse_address_search(self, lat: float, lng: float) -> str:
        """
        Look up the nearest address description for given latitude and longitude.
        """
        try:
            response = self.get("v3_1/reverse", params={"lat": lat, "lon": lng})
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "Couldn't retrieve locatieserver reverse lookup data",
                extra={"lat": lat, "lng": lng},
                exc_info=exc,
            )
            return ""

        docs: list[dict] = response.json().get("response", {}).get("docs")
        # no response with docs: return empty
        if not docs:
            return ""

        return docs[0].get("weergavenaam", "")
