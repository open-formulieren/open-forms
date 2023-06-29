from .base import Component
from .dates import DatePickerConfig


class CosignComponent(Component):
    authPlugin: str


class DateComponent(Component):
    datePicker: DatePickerConfig | None
