from typing import Literal, TypedDict

from .base import Component, OptionDict
from .dates import DatePickerConfig


class FileConfig(TypedDict):
    allowedTypesLabels: list[str]


class FileComponent(Component):
    storage: Literal["url"]
    url: str
    useConfigFiletypes: bool
    filePattern: str
    file: FileConfig


class RadioComponent(Component):
    values: list[OptionDict]


class ContentComponent(Component):
    html: str


class DatetimeComponent(Component):
    datePicker: DatePickerConfig | None
