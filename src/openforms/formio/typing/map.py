from typing import Literal, NotRequired, TypedDict


class MapInitialCenter(TypedDict):
    lat: NotRequired[float]
    lng: NotRequired[float]


class MapInteractions(TypedDict):
    marker: bool
    polygon: bool
    polyline: bool


class Overlay(TypedDict):
    uuid: str
    label: str
    type: Literal["wms", "wfs"]
    layers: list[str]
