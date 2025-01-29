from typing import Literal, NotRequired, TypedDict

from .base import Component, OptionDict
from .dates import DatePickerConfig


class TextFieldComponent(Component):
    pass


class FileConfig(TypedDict):
    allowedTypesLabels: list[str]
    type: NotRequired[list[str]]


class FileComponent(Component):
    storage: Literal["url"]
    url: str
    useConfigFiletypes: bool
    filePattern: str
    file: FileConfig
    maxNumberOfFiles: NotRequired[int]


class FileData(TypedDict):
    url: str
    form: Literal[""]
    name: str
    size: int
    baseUrl: str
    project: Literal[""]


class SingleFileValue(TypedDict):
    # Source of truth: https://github.com/open-formulieren/types/blob/main/src/formio/components/file.ts
    name: str
    originalName: str
    size: int
    storage: Literal["url"]
    type: str
    url: str
    data: FileData


type FileValue = list[SingleFileValue]


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
