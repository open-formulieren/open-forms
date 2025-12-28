from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal, Self

from openforms.utils.date import datetime_in_amsterdam

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Key,
    Prefill,
    Registration,
    TranslatedErrors,
)


class FormioDate(date):
    @classmethod
    def fromstr(cls, datestr: str) -> Self | None:
        # FIXME: this doesn't work - `None` does not satisfy the `FormioDate` type and
        # msgspec rejects it
        if datestr == "":
            return None
        if "T" in datestr:
            # convert to NL timezone, assuming the date should be in NL
            dt = datetime_in_amsterdam(datetime.fromisoformat(datestr))
            return cls(year=dt.year, month=dt.month, day=dt.day)
        return cls.fromisoformat(datestr)


class NoDateConstraint(FormioStruct, tag="", tag_field="mode"):
    pass


class FixedValueDateConstraint(FormioStruct, tag="fixedValue", tag_field="mode"):
    pass


class FutureDateConstraint(FormioStruct, tag="future", tag_field="mode"):
    include_today: bool | None = None


class PastDateConstraint(FormioStruct, tag="past", tag_field="mode"):
    include_today: bool | None = None


class DateConstraintDelta(FormioStruct):
    years: int | None
    months: int | None
    days: int | None


class RelativeDateConstraint(
    FormioStruct, kw_only=True, tag="relativeToVariable", tag_field="mode"
):
    variable: Key | None = None
    delta: DateConstraintDelta
    operator: Literal["add", "subtract"] = "add"


class DateExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip", "placeholder"]]
):
    widget: Literal["inputGroup", "datePicker"] = "datePicker"
    min_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | FutureDateConstraint
        | RelativeDateConstraint
        | None
    ) = None
    max_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | PastDateConstraint
        | RelativeDateConstraint
        | None
    ) = None


type DateValidatorKeys = Literal["required", "minDate", "maxDate", "invalid_date"]


class DateValidate(FormioStruct):
    required: bool = False
    min_date: date | None = None
    max_date: date | None = None


class PickerCustomOptions(FormioStruct, frozen=True):
    allow_invalid_preload: bool = True


class DatePickerConfig(FormioStruct):
    # See https://github.com/open-formulieren/types/blob/44291a9388174ef2525817b46db8e16ed1e0d8aa/src/formio/dates.ts#L75
    show_weeks: bool
    starting_day: Literal[0, 1, 2, 3, 4, 5, 6]
    # TODO should be date, but those unions are not supported, however - we probably don't
    # even support this anyway
    init_date: Literal[""]
    min_mode: Literal["day", "month", "year"]
    max_mode: Literal["day", "month", "year"]
    year_rows: int
    year_columns: int
    min_date: FormioDate | None
    max_date: FormioDate | None


# FIXME: should convert str -> date, but can't do `date | Literal[""] | None` in msgspec
# due to everything being string based and empty string not being parseable as a date.
type DateValue = str


class Date(Component, tag="date"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # TODO not relevant anymore in new renderer
    custom_options: PickerCustomOptions = PickerCustomOptions()
    date_picker: DatePickerConfig | None = None
    default_value: DateValue | Sequence[DateValue] = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[DateValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: DateExtensions | None = None
    placeholder: str = ""
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[DateValidatorKeys] | None = None
    validate: DateValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
    multiple: bool = False

    def __post_init__(self):
        # TODO: remove the string types when we have proper date parsing
        match (self.multiple, self.default_value):
            case True, str() | date() | None:
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a date default_value when multiple=False"
                )
