from typing_extensions import NotRequired

from .base import Component
from .dates import DatePickerConfig, DatePickerCustomOptions


class DateComponent(Component):
    datePicker: NotRequired[DatePickerConfig]
    customOptions: NotRequired[DatePickerCustomOptions]
