"""
Base types for more specific component types.

These are common ancestors for all specific component types.
"""

from typing import Literal, NotRequired, TypedDict

from openforms.typing import JSONValue

from ..constants import DataSrcOptions
from .dates import DateConstraintConfiguration

type TranslationsDict = dict[str, dict[str, str]]


class Validate(TypedDict, total=False):
    # all attributes are optional, some attributes are only present with certain
    # component types (which we cannot express in our current type definitions)
    required: bool
    maxLength: int
    pattern: str
    min: int | float
    max: int | float
    minTime: str
    maxTime: str
    plugins: list[str]


# Custom validation for AddressNL sub components
class ComponentValidation(TypedDict):
    validate: Validate
    translatedErrors: TranslationsDict


class AddressValidationComponents(TypedDict):
    postcode: NotRequired[ComponentValidation]
    city: NotRequired[ComponentValidation]


class OpenFormsConfig(TypedDict):
    widget: NotRequired[str]
    minDate: NotRequired[DateConstraintConfiguration | None]
    maxDate: NotRequired[DateConstraintConfiguration | None]
    translations: NotRequired[TranslationsDict]
    components: NotRequired[AddressValidationComponents]
    requireVerification: NotRequired[bool]
    dataSrc: NotRequired[DataSrcOptions]
    code: NotRequired[str]
    service: NotRequired[str]


class OpenFormsOptionExtension(TypedDict):
    translations: NotRequired[TranslationsDict]


class OptionDict(TypedDict):
    """
    Value as used in a select/radio/... component.

    These are (value, label) pairs, with a system value mapped to a human readable
    label used for display.
    """

    value: str
    label: str
    description: NotRequired[str]
    openForms: NotRequired[OpenFormsOptionExtension]


class PrefillConfiguration(TypedDict):
    plugin: str
    attribute: str
    identifierRole: Literal["main", "authorizee"]


class Component(TypedDict):
    """
    A formio component definition.

    Components are of a particular type, used as unique lookup keys in registries.
    Additionally, some common properties are (usually) present that also influence
    certain logic.
    """

    type: str
    key: str
    label: str
    multiple: NotRequired[bool]
    tooltip: NotRequired[str]
    description: NotRequired[str]
    hidden: NotRequired[bool]
    defaultValue: NotRequired[JSONValue]
    validate: NotRequired[Validate]
    prefill: NotRequired[PrefillConfiguration]
    openForms: NotRequired[OpenFormsConfig]
    autocomplete: NotRequired[str]
    dataType: NotRequired[Literal["string"]]


class FormioConfiguration(TypedDict):
    components: list[Component]
