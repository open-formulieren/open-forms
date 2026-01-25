from __future__ import annotations

from collections.abc import Sequence
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

type NumberValidatorKeys = Literal["required", "min", "max"]
type NumberExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class NumberValidate(FormioStruct):
    required: bool = False
    min: float | None = None
    max: float | None = None
    plugins: Sequence[str] = []


class Number(Component, tag="number"):
    allow_negative: bool = False
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    decimal_limit: Annotated[int, Meta(ge=0, le=9)] | None = None
    default_value: float | None = None
    description: str = ""
    errors: Errors[NumberValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: NumberExtensions | None = None
    prefix: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    suffix: str = ""
    tooltip: str = ""
    translated_errors: TranslatedErrors[NumberValidatorKeys] | None = None
    validate: NumberValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
