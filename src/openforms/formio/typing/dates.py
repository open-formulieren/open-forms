"""
Types for our date/datetime validation extension.
"""

from typing import Literal, TypedDict


class DateConstraintDelta(TypedDict):
    years: int | None
    months: int | None
    days: int | None


class DateConstraintConfiguration(TypedDict):
    mode: Literal["", "fixedValue", "future", "past", "relativeToVariable"]
    includeToday: bool | None
    variable: str | None
    delta: DateConstraintDelta | None
    operator: Literal["add", "subtract"] | None


class DatePickerConfig(TypedDict):
    minDate: str | None
    maxDate: str | None
