"""
Types for our date/datetime validation extension.
"""

from typing import Literal, TypedDict

from typing_extensions import NotRequired


class DateConstraintDelta(TypedDict):
    years: NotRequired[int | None]
    months: NotRequired[int | None]
    days: NotRequired[int | None]


class DateConstraintConfiguration(TypedDict):
    mode: Literal["", "fixedValue", "future", "past", "relativeToVariable"]
    includeToday: NotRequired[bool | None]
    variable: NotRequired[str | None]
    delta: NotRequired[DateConstraintDelta | None]
    operator: NotRequired[Literal["add", "subtract"] | None]


class DatePickerConfig(TypedDict):
    minDate: str | None
    maxDate: str | None
