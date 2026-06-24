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

type CustomerProfileValidatorKeys = Literal["required"]

type CustomerProfileExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]

type DigitalAddressType = Literal["email", "phoneNumber"]


class DigitalAddress(FormioStruct):
    address: str
    type: DigitalAddressType
    preference_update: Literal["useOnlyOnce", "isNewPreferred"] = "useOnlyOnce"


class CustomerProfileValidate(FormioStruct):
    required: bool = False


class CustomerProfile(Component, tag="customerProfile"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: Sequence[DigitalAddress] | None = None
    description: str = ""
    digital_address_types: Sequence[DigitalAddressType] = []
    errors: Errors[CustomerProfileValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: CustomerProfileExtensions | None = None
    registration: Registration | None = None
    should_update_customer_data: bool = True
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CustomerProfileValidatorKeys] | None = None
    validate: CustomerProfileValidate | None = None
