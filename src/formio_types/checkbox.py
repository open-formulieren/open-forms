from __future__ import annotations

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
type CheckboxValidatorKeys = str

type CheckboxExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class CheckboxValidate(FormioStruct):
    required: bool = False


class Checkbox(Component, tag="checkbox"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: bool = False
    description: str = ""
    errors: Errors[CheckboxValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: CheckboxExtensions | None = None
    placeholder: str = ""  # TODO: remove from TS types
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CheckboxValidatorKeys] | None = None
    validate: CheckboxValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
