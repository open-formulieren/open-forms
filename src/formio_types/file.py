from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal

import msgspec
import structlog
from msgspec import Meta
from typing_extensions import deprecated

from openforms.typing import VariableValue

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)
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


type FileTranslatableProperties = Literal["label", "description", "tooltip"]


class FileExtensions(BaseOpenFormsExtensions[FileTranslatableProperties]):
    image: ImageOptions | None = None


class FileValidate(FormioStruct):
    required: bool = False


# class FileComponentOptions(FormioStruct, frozen=True):
#     with_credentials: bool = True  # can't use Literal[True]


class FileOptions(FormioStruct):
    allowed_types_labels: list[str] = []
    name: str = ""
    type: list[MimeType]


class FileRegistrationDocumentTypeCatalogue(FormioStruct):
    domain: str = ""
    rsin: str = ""


class FileRegistrationDocumentType(FormioStruct):
    catalogue: FileRegistrationDocumentTypeCatalogue | None = None
    description: str = ""


@deprecated("Component-level registration options are no longer used")
class Registration(FormioStruct):
    bronorganisatie: str = ""
    doc_vertrouwelijkheidaanduiding: str = ""
    titel: str = ""
    document_type: FileRegistrationDocumentType | None = None
    informatieobjecttype: str = ""


class File(Component, tag="file"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    description: str = ""
    errors: Errors[FileValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    file: FileOptions
    file_max_size: str = ""  # e.g. 10MB
    file_pattern: str
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    max_number_of_files: int | None = None
    multiple: bool = False
    open_forms: FileExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[FileValidatorKeys] | None = None
    use_config_filetypes: bool = False
    validate: FileValidate = msgspec.field(default_factory=FileValidate)

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("file does not support prefill")

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
