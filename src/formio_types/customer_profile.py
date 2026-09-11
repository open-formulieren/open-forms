from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

import msgspec

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

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
    confirmation_recipient: bool = False
    # default_value: Sequence[DigitalAddress] | None = None
    description: str = ""
    digital_address_types: Sequence[DigitalAddressType] = []
    errors: Errors[CustomerProfileValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: CustomerProfileExtensions | None = None
    registration: Registration | None = None
    should_update_customer_data: bool = True
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CustomerProfileValidatorKeys] | None = None
    validate: CustomerProfileValidate = msgspec.field(
        default_factory=CustomerProfileValidate
    )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
