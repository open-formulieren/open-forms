from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import ClassVar, Literal

import msgspec

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

type PhoneNumberValidatorKeys = Literal["required", "pattern"]

type PhoneNumberTranslatableProperties = Literal["label", "description", "tooltip"]

PhoneNumberExtensions = BaseOpenFormsExtensions[PhoneNumberTranslatableProperties]


class PhoneNumberValidate(FormioStruct):
    required: bool = False
    pattern: str = ""
    plugins: Sequence[str] = []
    # not in the TS type defs!
    max_length: int | None = None


class PhoneNumber(Component, tag="phoneNumber"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[PhoneNumberValidatorKeys] | None = None
    hidden: bool = False
    input_mask: None = None
    is_sensitive_data: bool = True
    label: str
    open_forms: PhoneNumberExtensions | None = None
    placeholder: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[PhoneNumberValidatorKeys] | None = None
    validate: PhoneNumberValidate | None = None
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
