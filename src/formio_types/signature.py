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

type SignatureValidatorKeys = Literal["required"]
type SignatureExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip", "footer"]
]


class SignatureValidate(FormioStruct):
    required: bool = False


class Signature(Component, tag="signature"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str = ""  # base64 data:image/png URI
    description: str = ""
    errors: Errors[SignatureValidatorKeys] | None = None
    footer: str = ""
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: SignatureExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SignatureValidatorKeys] | None = None
    validate: SignatureValidate | None = None
