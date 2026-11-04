from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal

import msgspec
from msgspec import Meta
from typing_extensions import deprecated

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    TranslatedErrors,
)
from ..templating import TestWithTrace

type MimeType = Annotated[str, Meta(pattern=r"(\w+/[\w.*\-_]+)|(\*)")]

type FileValidatorKeys = Literal["required"]


class ResizeOptions(FormioStruct):
    apply: bool = False
    height: int | msgspec.UnsetType = msgspec.UNSET
    width: int | msgspec.UnsetType = msgspec.UNSET


class ImageOptions(FormioStruct):
    resize: ResizeOptions | msgspec.UnsetType = msgspec.UNSET


type FileTranslatableProperties = Literal["label", "description", "tooltip"]


@deprecated("Should be moved to openForms namespace")
class LegacyFileExtensions(FormioStruct):
    image: ImageOptions | msgspec.UnsetType = msgspec.UNSET


class FileExtensions(BaseOpenFormsExtensions[FileTranslatableProperties]):
    soft_required: bool = False


class FileValidate(FormioStruct):
    required: bool = False


class FileOptions(FormioStruct):
    allowed_types_labels: Sequence[str] = []
    name: str = ""
    type: Sequence[MimeType]


class File(Component, tag="file"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    description: str = ""
    errors: Errors[FileValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    file: FileOptions
    file_max_size: str = ""  # e.g. 10MB
    file_pattern: str
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    max_number_of_files: int | None = None
    multiple: bool = False
    of: LegacyFileExtensions | msgspec.UnsetType = msgspec.UNSET
    open_forms: FileExtensions | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[FileValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    use_config_filetypes: bool = False
    validate: FileValidate = msgspec.field(default_factory=FileValidate)

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
