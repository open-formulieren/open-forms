from .base import Component
from .dates import DatePickerConfig


class DateComponent(Component):
    datePicker: DatePickerConfig | None
