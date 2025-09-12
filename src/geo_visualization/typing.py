from typing import Literal, TypedDict

type Coordinates = tuple[float, float]


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
