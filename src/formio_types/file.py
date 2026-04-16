from __future__ import annotations

from typing import Annotated, Literal

from msgspec import Meta

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

type MimeType = Annotated[str, Meta(pattern=r"(\w+/[\w.*\-_]+)|(\*)")]

type FileValidatorKeys = Literal["required"]


class FileUploadNestedData(FormioStruct):
    base_url: str
    form: Literal[""] = ""
    name: str
    project: Literal[""] = ""
    size: Annotated[int, Meta(ge=0)]
    url: str


class FileUploadData(FormioStruct):
    data: FileUploadNestedData
    name: str
    original_name: str
    size: Annotated[int, Meta(ge=0)]
    storage: Literal["url"] = "url"
    type: MimeType
    url: str

    def __post_init__(self):
        if not self.url == self.data.url:
            raise ValueError("'url' values are expected to be identical.")
        if not self.size == self.data.size:
            raise ValueError("'size' values are expected to be identical.")


class ResizeOptions(FormioStruct):
    apply: bool = False
    height: int | None = None
    width: int | None = None


class ImageOptions(FormioStruct):
    resize: ResizeOptions | None = None


class FileExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]],
):
    image: ImageOptions | None = None


class FileValidate(FormioStruct):
    required: bool = False


class FileComponentOptions(FormioStruct, frozen=True):
    with_credentials: bool = True  # can't use Literal[True]


class FileOptions(FormioStruct):
    allowed_types_labels: list[str] = []
    name: str = ""
    type: list[MimeType]


class File(Component, tag="file"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: list[FileUploadData] | None = None
    description: str = ""
    errors: Errors[FileValidatorKeys] | None = None
    file: FileOptions
    file_max_size: str = ""  # e.g. 10MB
    file_pattern: str
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    max_number_of_files: int | None = None
    multiple: bool = False
    open_forms: FileExtensions | None = None
    options: FileComponentOptions | Literal['{"withCredentials": true}'] = (
        FileComponentOptions()
    )
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    storage: Literal["url"] = "url"
    tooltip: str = ""
    translated_errors: TranslatedErrors[FileValidatorKeys] | None = None
    url: str = ""
    use_config_filetypes: bool = False
    validate: FileValidate | None = None
    webcam: bool = False  # can't use Literal[False]

    def __post_init__(self):
        match self.options:
            case str():
                self.options = FileComponentOptions()
            case _:  # pragma: no cover
                pass
