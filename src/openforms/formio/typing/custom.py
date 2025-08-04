from typing import NotRequired

from .base import Component
from .dates import DatePickerConfig, DatePickerCustomOptions
from .map import MapInitialCenter, MapInteractions


class DateComponent(Component):
    datePicker: NotRequired[DatePickerConfig]
    customOptions: NotRequired[DatePickerCustomOptions]


class AddressNLComponent(Component):
    deriveAddress: bool


class MapComponent(Component):
    useConfigDefaultMapSettings: bool
    defaultZoom: NotRequired[int]
    initialCenter: NotRequired[MapInitialCenter]
    tileLayerIdentifier: NotRequired[str]
    interactions: MapInteractions
    # The tileLayerUrl will be dynamically generated from the tileLayerIdentifier
    tileLayerUrl: NotRequired[str]


class ChildrenComponent(Component):
    enableSelection: bool
