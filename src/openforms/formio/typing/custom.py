from typing import NotRequired

from .base import Component
from .dates import DatePickerConfig, DatePickerCustomOptions


class DateComponent(Component):
    datePicker: NotRequired[DatePickerConfig]
    customOptions: NotRequired[DatePickerCustomOptions]


class AddressNLComponent(Component):
    deriveAddress: bool
