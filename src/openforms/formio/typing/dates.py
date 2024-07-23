"""
Types for our date/datetime validation extension.
"""

from typing import Literal, NotRequired, TypedDict


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


class DatePickerCustomOptions(TypedDict):
    allowInvalidPreload: NotRequired[bool]


class DatePickerConfig(TypedDict):
    # NOTE: these strings can be a date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:mm:ss)
    # ISO-8601 string! Even the date component uses datetimes under the hood because
    # Javascript only has a Date type that covers both, and that leaks into our form
    # builder and backend logic doing dynamic things.
    showWeeks: NotRequired[bool]
    startingDay: NotRequired[Literal[0, 1, 2, 3, 4, 5, 6]]
    initDate: NotRequired[str]
    minMode: NotRequired[Literal["day", "month", "year"]]
    maxMode: NotRequired[Literal["day", "month", "year"]]
    yearRows: NotRequired[int]
    yearColumns: NotRequired[int]
    minDate: str | None
    maxDate: str | None
