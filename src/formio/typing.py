from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from typing import TypedDict

from dateutil.relativedelta import relativedelta

type JSONPrimitive = str | int | float | bool | None
type Value = JSONPrimitive | date | datetime | time | relativedelta

type ComponentValue = Value | Mapping[str, ComponentValue] | Sequence[ComponentValue]
"""
Values in the Python domain that may be assigned to formio components.
"""


class ComponentDict(TypedDict):
    """
    Ultra-minimal typed-dict definition for a Formio component definition.

    Intended to be a simple guard for conversion functions. This should not be extended
    or have any complexity added to it.
    """

    type: str
    key: str
    # no label - layout components like content/columns don't have a label
