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

type CurrencyValidatorKeys = Literal["required", "min", "max"]
type CurrencyExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class CurrencyValidate(FormioStruct):
    required: bool = False
    min: float | None = None
    max: float | None = None


class Currency(Component, tag="currency"):
    allow_negative: bool = False
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    currency: Literal["EUR"] = "EUR"
    decimal_limit: Annotated[int, Meta(ge=0, le=9)] | None = None
    default_value: float | None = None
    description: str = ""
    errors: Errors[CurrencyValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: CurrencyExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CurrencyValidatorKeys] | None = None
    validate: CurrencyValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
