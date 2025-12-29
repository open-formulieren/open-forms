from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal, Self, assert_never

from msgspec import field

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


class NoDateConstraint(FormioStruct, tag="", tag_field="mode"):
    pass


class FixedValueDateConstraint(FormioStruct, tag="fixedValue", tag_field="mode"):
    pass


class FutureDateTimeConstraint(FormioStruct, tag="future", tag_field="mode"):
    pass


class PastDateTimeConstraint(FormioStruct, tag="past", tag_field="mode"):
    pass


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


class DateTimeExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip", "placeholder"]]
):
    min_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | FutureDateTimeConstraint
        | RelativeDateConstraint
        | None
    ) = None
    max_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | PastDateTimeConstraint
        | RelativeDateConstraint
        | None
    ) = None


type DateTimeValidatorKeys = Literal[
    "required", "minDate", "maxDate", "invalid_datetime"
]


class DateTimeValidate(FormioStruct):
    required: bool = False
    min_date: datetime | None = None
    max_date: datetime | None = None


class PickerCustomOptions(FormioStruct, frozen=True):
    allow_invalid_preload: bool = True


class DateTimePickerConfig(FormioStruct):
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
    # TODO: should be datetime instead of str, but they're not all valid RFC3339 encoded.
    min_date: str | None
    # TODO: should be datetime instead of str, but they're not all valid RFC3339 encoded.
    max_date: str | None


class FormioDateTime:
    actual_value: datetime | Sequence[datetime] | None

    def __init__(self, actual_value: datetime | Sequence[datetime] | None):
        self.actual_value = actual_value

    @classmethod
    def fromstr(cls, raw_value: str | Sequence[str]) -> Self:
        match raw_value:
            case "":
                return cls(actual_value=None)
            case str():
                return cls(actual_value=datetime.fromisoformat(raw_value))
            case Sequence():
                actual_value = [datetime.fromisoformat(x) for x in raw_value]
                return cls(actual_value=actual_value)
            case _:  # pragma: no cover
                assert_never(raw_value)

    # # doesn't work, descriptors don't seem supported :(
    # # https://github.com/jcrist/msgspec/issues/864
    # def __get__(self, obj, objtype=None):
    #     breakpoint()
    #     return self.actual_value

    def __eq__(self, other) -> bool:
        return self.actual_value == other


class DateTime(Component, tag="datetime"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # TODO not relevant anymore in new renderer
    custom_options: PickerCustomOptions = PickerCustomOptions()
    date_picker: DateTimePickerConfig | None = None
    default_value: FormioDateTime | None = field(
        default_factory=lambda: FormioDateTime(actual_value=None)
    )
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[DateTimeValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: DateTimeExtensions | None = None
    placeholder: str = ""
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[DateTimeValidatorKeys] | None = None
    validate: DateTimeValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
    multiple: bool = False

    def __post_init__(self):
        match (self.multiple, self.default_value):
            case True, FormioDateTime(actual_value=datetime() | None):
                raise ValueError("You must pass a list of values when multiple=True")
            case False, FormioDateTime(actual_value=Sequence()):
                raise ValueError(
                    "You must pass a date default_value when multiple=False"
                )
