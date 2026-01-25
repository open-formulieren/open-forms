from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

# FIXME: should be Literal["required"], but there is garbage data
type EmailValidatorKeys = str


class EmailExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]]
):
    require_verification: bool = False


class EmailValidate(FormioStruct):
    required: bool = False
    max_length: int | None = None
    plugins: Sequence[str] = []


class Email(Component, tag="email"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    confirmation_recipient: bool = False
    default_value: str | Sequence[str] = ""
    description: str = ""
    errors: Errors[EmailValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: EmailExtensions | None = None
    placeholder: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[EmailValidatorKeys] | None = None
    validate: EmailValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
    multiple: bool = False

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
