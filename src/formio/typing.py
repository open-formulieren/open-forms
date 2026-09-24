from collections.abc import Mapping, Sequence
from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta

type JSONPrimitive = str | int | float | bool | None
type Value = JSONPrimitive | date | datetime | time | relativedelta

type ComponentValue = Value | Mapping[str, ComponentValue] | Sequence[ComponentValue]
"""
Values in the Python domain that may be assigned to formio components.
"""
