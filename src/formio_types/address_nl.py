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


class AddressNLExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]]
):
    components: AddressComponents | None = None


class AddressNLValidate(FormioStruct):
    required: bool = False


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
    default_value: AddressData | None = None
    derive_address: bool = False
    description: str = ""
    errors: Errors[AddressNLValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    layout: Literal["singleColumn", "doubleColumn"] = "doubleColumn"
    open_forms: AddressNLExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[AddressNLValidatorKeys] | None = None
    validate: AddressNLValidate | None = None
