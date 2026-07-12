from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Annotated, ClassVar, Literal

import msgspec
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

type TextareaValidatorKeys = Literal["required", "maxLength", "pattern"]

type TextareaTranslatableProperties = Literal[
    "label", "description", "tooltip", "placeholder"
]

TextareaExtensions = BaseOpenFormsExtensions[TextareaTranslatableProperties]


class TextareaValidate(FormioStruct):
    required: bool = False
    max_length: int | None = None
    pattern: str = ""


class Textarea(Component, tag="textarea"):
    autocomplete: str = ""
    auto_expand: bool = False
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TextareaValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: TextareaExtensions | None = None
    placeholder: str = ""
    registration: Registration | None = None
    rows: Annotated[int, Meta(ge=1)] | None = None
    show_char_count: bool = False
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TextareaValidatorKeys] | None = None
    validate: TextareaValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
    multiple: bool = False

    SUPPORTED_TEMPLATE_ATTRIBUTES: ClassVar[Collection[str]] = frozenset(
        ("label", "description", "placeholder", "tooltip", "default_value")
    )

    def __post_init__(self):
        match (self.multiple, self.default_value):
            case True, str():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )
