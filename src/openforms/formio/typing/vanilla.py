from typing import Literal, TypedDict

from typing_extensions import NotRequired

from .base import Component, OptionDict
from .dates import DatePickerConfig


class TextFieldComponent(Component):
    pass


class FileConfig(TypedDict):
    allowedTypesLabels: list[str]


class FileComponent(Component):
    storage: Literal["url"]
    url: str
    useConfigFiletypes: bool
    filePattern: str
    file: FileConfig


class SelectData(TypedDict, total=False):
    values: list[OptionDict]


class SelectComponent(Component):
    data: SelectData


class RadioComponent(Component):
    values: list[OptionDict]


class SelectBoxesComponent(Component):
    values: list[OptionDict]


class ContentComponent(Component):
    html: str


class DatetimeComponent(Component):
    datePicker: NotRequired[DatePickerConfig | None]


class FieldsetComponent(Component):
    components: list[Component]


class Column(TypedDict):
    size: int
    sizeMobile: int
    components: list[Component]


class ColumnsComponent(Component):
    columns: list[Column]


class EditGridComponent(Component):
    groupLabel: NotRequired[str]
    components: list[Component]
