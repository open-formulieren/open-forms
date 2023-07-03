"""
Base types for more specific component types.

These are common ancestors for all specific component types.
"""

# TODO: on python 3.11+ we can use typing.NotRequired to mark keys that may be absent.
# For now at least, we use total=False.

from typing import TypedDict

from openforms.typing import JSONValue

from .dates import DateConstraintConfiguration


class Validate(TypedDict, total=False):
    required: bool
    maxLength: int
    min: int | float
    max: int | float


class OpenFormsConfig(TypedDict, total=False):
    widget: str
    minDate: DateConstraintConfiguration | None
    maxDate: DateConstraintConfiguration | None


class OptionDict(TypedDict):
    """
    Value as used in a select/radio/... component.

    These are (value, label) pairs, with a system value mapped to a human readable
    label used for display.
    """

    value: str
    label: str


class PrefillConfiguration(TypedDict):
    plugin: str
    attribute: str


class Component(TypedDict, total=False):
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
    multiple: bool
    hidden: bool
    defaultValue: JSONValue
    validate: Validate
    prefill: PrefillConfiguration
    openForms: OpenFormsConfig
    autocomplete: str
