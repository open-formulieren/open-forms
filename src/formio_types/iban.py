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

type IbanValidatorKeys = Literal["required"]
type IbanExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class IbanValidate(FormioStruct):
    required: bool = False


class Iban(Component, tag="iban"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    description: str = ""
    errors: Errors[IbanValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: IbanExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[IbanValidatorKeys] | None = None
    validate: IbanValidate | None = None
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
