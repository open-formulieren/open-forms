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

type CosignV1Extensions = BaseOpenFormsExtensions[Literal["label", "description"]]


class CosignV1(Component, tag="coSign"):
    auth_plugin: str
    description: str = ""
    hidden: bool = False
    label: str
    open_forms: CosignV1Extensions | None = None


type CosignV2ValidatorKeys = Literal["required"]
type CosignV2Extensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class CosignV2Validate(FormioStruct):
    required: bool = False


class CosignV2(Component, tag="cosign"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    description: str = ""
    errors: Errors[CosignV2ValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: CosignV2Extensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CosignV2ValidatorKeys] | None = None
    validate: CosignV2Validate | None = None
    validate_on: Literal["blur"] = "blur"
