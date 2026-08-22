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

type AddressNLValidatorKeys = Literal["required"]


class CityValidate(FormioStruct):
    pattern: str = ""


class CityOptions(FormioStruct):
    errors: Errors[Literal["pattern"]] | None = None
    translated_errors: TranslatedErrors[Literal["pattern"]] | None = None
    validate: CityValidate | None = None


class PostcodeValidate(FormioStruct):
    pattern: str = ""


class PostcodeOptions(FormioStruct):
    errors: Errors[Literal["pattern"]] | None = None
    translated_errors: TranslatedErrors[Literal["pattern"]] | None = None
    validate: CityValidate | None = None


class AddressComponents(FormioStruct):
    city: CityOptions | None = None
    postcode: PostcodeOptions | None = None


type AddressNLTranslatableProperties = Literal["label", "description", "tooltip"]


class AddressNLExtensions(BaseOpenFormsExtensions[AddressNLTranslatableProperties]):
    components: AddressComponents | None = None


class AddressNLValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class AddressData(FormioStruct):
    auto_populated: bool = False
    city: str = ""
    house_letter: str
    house_number: str
    house_number_addition: str
    postcode: str
    secret_street_city: str = ""
    street_name: str = ""


class AddressNL(Component, tag="addressNL"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # TODO: remove, default value is not exposed in the formio-builder
    # default_value: AddressData | None = None
    derive_address: bool = False
    description: str = ""
    errors: Errors[AddressNLValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    hide_label: bool = False
    is_sensitive_data: bool = True
    label: str
    layout: Literal["singleColumn", "doubleColumn"] = "doubleColumn"
    open_forms: AddressNLExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[AddressNLValidatorKeys] | None = None
    validate: AddressNLValidate = msgspec.field(default_factory=AddressNLValidate)

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
