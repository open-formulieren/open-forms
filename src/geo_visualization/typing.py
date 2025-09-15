from typing import Literal, TypedDict

type Coordinates = tuple[float, float]

type SupportedCrs = Literal["EPSG:28992"]
"""
Coordinate reference systems that we support.
"""


class PointGeometry(TypedDict):
    type: Literal["Point"]
    coordinates: Coordinates


class LineStringGeometry(TypedDict):
    type: Literal["LineString"]
    coordinates: list[Coordinates]


class PolygonGeometry(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[Coordinates]]


type GeoJson = PointGeometry | LineStringGeometry | PolygonGeometry


class Overlay(TypedDict):
    type: Literal["wms", "wfs"]
    url: str
    layers: list[str]
