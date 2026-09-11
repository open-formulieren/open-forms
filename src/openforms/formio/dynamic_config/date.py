import operator
from datetime import date, datetime, time
from typing import assert_never

from django.utils import timezone

from dateutil.relativedelta import relativedelta

from formio_types import Date, DateTime
from formio_types.date import (
    DateConstraintDelta,
    DatePickerConfig,
    FixedValueDateConstraint,
    FutureDateConstraint,
    NoDateConstraint,
    PastDateConstraint,
    RelativeDateConstraint,
)
from formio_types.datetime import (
    DateConstraintDelta as DateTimeConstraintDelta,
    DateTimePickerConfig,
    FixedValueDateConstraint as FixedValueDateTimeConstraint,
    FutureDateTimeConstraint,
    NoDateConstraint as NoDateTimeConstraint,
    PastDateTimeConstraint,
    RelativeDateConstraint as RelativeDateTimeConstraint,
)

from ..datastructures import FormioData

NOW_VARIABLE = "now"


def mutate(component: Date | DateTime, data: FormioData) -> None:
    if not (of_config := component.open_forms):
        return

    fields = ("min_date", "max_date")
    min_date_constraint = of_config.min_date
    max_date_constraint = of_config.max_date

    # looks odd, but not using `getattr` makes it possible for the type checker to infer
    # the right types :)
    for field, _constraint in zip(
        fields, (min_date_constraint, max_date_constraint), strict=True
    ):
        match _constraint:
            case (
                None
                | NoDateConstraint()
                | NoDateTimeConstraint()
                # for fixed values, the constraint is already set in the date_picker
                # property
                | FixedValueDateConstraint()
                | FixedValueDateTimeConstraint()
            ):
                continue
            # normalize to an equivalent relative delta expression
            case FutureDateConstraint() | PastDateConstraint():
                constraint = convert_date_constraint_to_relative_delta(_constraint)
            # normalize to an equivalent relative delta expression
            case FutureDateTimeConstraint() | PastDateTimeConstraint():
                constraint = convert_datetime_constraint_to_relative_delta(_constraint)
            # already in the right shape for further processing
            case RelativeDateConstraint() | RelativeDateTimeConstraint():
                constraint = _constraint
            case _:  # pragma: no cover
                assert_never(_constraint)

        value = calculate_delta(component, constraint, data)

        if value and isinstance(value, datetime):
            value = value.isoformat()

        if component.date_picker is None:
            match component:
                case Date():
                    component.date_picker = DatePickerConfig()
                case DateTime():
                    component.date_picker = DateTimePickerConfig()
                case _:  # pragma: no cover
                    assert_never(field)

        match field:
            case "min_date":
                component.date_picker.min_date = value
            case "max_date":
                component.date_picker.max_date = value
            case _:  # pragma: no cover
                assert_never(field)


def convert_date_constraint_to_relative_delta(
    constraint: FutureDateConstraint | PastDateConstraint,
) -> RelativeDateConstraint:
    match constraint:
        case FutureDateConstraint():
            operator = "add"
        case PastDateConstraint():
            operator = "subtract"
        case _:  # pragma: no cover
            assert_never(constraint)

    delta = DateConstraintDelta(
        years=0,
        months=0,
        days=0 if constraint.include_today else 1,
    )
    return RelativeDateConstraint(
        variable=NOW_VARIABLE,
        delta=delta,
        operator=operator,
    )


def convert_datetime_constraint_to_relative_delta(
    constraint: FutureDateTimeConstraint | PastDateTimeConstraint,
) -> RelativeDateTimeConstraint:
    match constraint:
        case FutureDateTimeConstraint():
            operator = "add"
        case PastDateTimeConstraint():
            operator = "subtract"
        case _:  # pragma: no cover
            assert_never(constraint)

    delta = DateTimeConstraintDelta(years=0, months=0, days=0)
    return RelativeDateTimeConstraint(
        variable=NOW_VARIABLE,
        delta=delta,
        operator=operator,
    )


def calculate_delta(
    component: Date | DateTime,
    constraint: RelativeDateConstraint | RelativeDateTimeConstraint,
    data: FormioData,
) -> datetime | None:
    if not (base_value := data.get(constraint.variable, None)):
        return None
    delta = relativedelta(
        years=constraint.delta.years or 0,
        months=constraint.delta.months or 0,
        days=constraint.delta.days or 0,
    )

    func = operator.add if constraint.operator == "add" else operator.sub
    value = func(base_value, delta)
    assert isinstance(value, date | datetime)

    if isinstance(component, DateTime):
        assert isinstance(value, datetime)
        # Truncate seconds/microseconds, because they can be problematic when comparing with variables like "now" which can have
        # seconds > 0 while the flatpickr editor always sets the seconds to 0. This means that if the datetime entered
        # by the user needs to be >= 2022-11-03T12:00:05Z and the user enters 2022-11-03 12:00, this will be outside
        # the configured min/max interval. Since for the flatpickr configuration this datetime is invalid, it is cleared
        # from the input field (i.e. - the value disappears in the frontend) and then the picker defaults to
        # the next year when opened again.
        value = value.replace(second=0, microsecond=0)
        return timezone.localtime(value)

    # convert to datetime at midnight for the date in the local timezone
    naive_value = datetime.combine(value, time.min)
    return timezone.make_aware(naive_value)
