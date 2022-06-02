"""
Type definitions to be used in type hints for Formio structures.

Formio components are JSON blobs adhering to a formio-specific schema. We define
(subsets) of these schema's to make it easier to reason about the code operating on
(parts of) the schema.
"""
# TODO: on python 3.11+ we can use typing.NotRequired to mark keys that may be absent
from typing import TypedDict

from openforms.typing import JSONValue


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


class Component(TypedDict):
    """
    A formio component definition.

    Components are of a particular type, used as unique lookup keys in registries.
    Additionally, some common properties are (usually) present that also influence
    certain logic.

    We deliberately document keys here that may be absent, because:

    * we don't run mypy (yet) and type hints are used as just hints/documentation
    * the mechanism to define this correctly is not fleshed out, see also
      https://discuss.python.org/t/pep-655-required-and-notrequired-for-typeddict/13817/3
    """

    type: str
    key: str
    label: str
    multiple: bool
    hidden: bool
    defaultValue: JSONValue
    prefill: PrefillConfiguration
