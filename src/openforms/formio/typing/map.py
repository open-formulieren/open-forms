from typing import Literal, NotRequired, TypedDict


class MapInitialCenter(TypedDict):
    lat: NotRequired[float]
    lng: NotRequired[float]


class MapInteractions(TypedDict):
    marker: bool
    polygon: bool
    polyline: bool


type OverlayType = Literal["wms", "wfs"]


class Overlay(TypedDict):
    uuid: str
    label: str
    url: NotRequired[str]  # added in dynamically
    type: OverlayType
    layers: list[str]
