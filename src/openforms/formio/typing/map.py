from typing import NotRequired, TypedDict


class MapInitialCenter(TypedDict):
    lat: NotRequired[float]
    lng: NotRequired[float]


class MapInteractions(TypedDict):
    marker: bool
    polygon: bool
    polyline: bool
