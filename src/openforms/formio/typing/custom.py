from typing_extensions import NotRequired

from .base import Component
from .dates import DatePickerConfig


class DateComponent(Component):
    datePicker: NotRequired[DatePickerConfig]
