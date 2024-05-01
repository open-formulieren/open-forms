"""
Base types for more specific component types.

These are common ancestors for all specific component types.
"""

# TODO: on python 3.11+ we can use typing.NotRequired to mark keys that may be absent.
# For now at least, we use total=False.

from typing import Literal, TypeAlias, TypedDict

from typing_extensions import NotRequired

from openforms.typing import JSONValue

from .dates import DateConstraintConfiguration

TranslationsDict: TypeAlias = dict[str, dict[str, str]]


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


class OpenFormsConfig(TypedDict):
    widget: NotRequired[str]
    minDate: NotRequired[DateConstraintConfiguration | None]
    maxDate: NotRequired[DateConstraintConfiguration | None]
    translations: NotRequired[TranslationsDict]


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
    openForms: NotRequired[OpenFormsOptionExtension]


class PrefillConfiguration(TypedDict):
    plugin: str
    attribute: str
    identifierRole: Literal["main", "authorised_person"]


class Component(TypedDict):
    """
    A formio component definition.

    Components are of a particular type, used as unique lookup keys in registries.
    Additionally, some common properties are (usually) present that also influence
    certain logic.

    We deliberately document keys here that may be absent, because:

    * we don't run mypy (yet) and type hints are used as just hints/documentation
    * NotRequired is only available in typing_extensions and Python 3.11+
    * The ``total=False`` matches Form.io's own typescript types where (almost) every
      property can be absent.
    """

    type: str
    key: str
    label: str
    multiple: NotRequired[bool]
    hidden: NotRequired[bool]
    defaultValue: NotRequired[JSONValue]
    validate: NotRequired[Validate]
    prefill: NotRequired[PrefillConfiguration]
    openForms: NotRequired[OpenFormsConfig]
    autocomplete: NotRequired[str]


class FormioConfiguration(TypedDict):
    components: list[Component]
