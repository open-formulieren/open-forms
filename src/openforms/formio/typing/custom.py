from typing import Literal, NotRequired, TypedDict

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


class ChildProperties(TypedDict):
    bsn: str
    first_names: str
    initials: str
    affixes: str
    last_name: str
    date_of_birth: str
    date_of_birth_precision: Literal["date", "year_month", "year"] | None
    selected: NotRequired[bool]
