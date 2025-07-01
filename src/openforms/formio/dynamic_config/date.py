import operator
from datetime import date, datetime, time
from typing import Any, TypedDict, cast

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from dateutil.relativedelta import relativedelta
from glom import assign, glom

from openforms.utils.date import parse_date

from ..datastructures import FormioData
from ..typing import DateComponent, DatetimeComponent
from ..typing.dates import DateConstraintConfiguration, DateConstraintDelta

NOW_VARIABLE = "now"


class DatePickerConfig(TypedDict):
    minDate: str | None
    maxDate: str | None


def mutate(component: DateComponent | DatetimeComponent, data: FormioData) -> None:
    for key in ("minDate", "maxDate"):
        config = cast(
            DateConstraintConfiguration,
            glom(component, f"openForms.{key}", default=None),
        )
        if config is None:
            continue

        if (mode := config.get("mode")) in [None, ""]:
            continue

        # formio has set the datePicker.{key} value
        if mode == "fixedValue":
            continue

        config = normalize_config(component, config)
        value = calculate_delta(component, config, data)
        if value and isinstance(value, datetime):
            value = value.isoformat()
        assign(component, f"datePicker.{key}", value, missing=dict)


def normalize_config(
    component: DateComponent | DatetimeComponent,
    config: DateConstraintConfiguration,
) -> DateConstraintConfiguration:
    assert "type" in component
    mode = config["mode"]
    assert mode in ("future", "past", "relativeToVariable")
    if mode == "relativeToVariable":
        return config

    # mode is now future or past -> convert that to a relative delta config
    config["mode"] = "relativeToVariable"
    config["variable"] = NOW_VARIABLE
    # With datetimes, it doesn't make sense to 'include today' or not when validating for future/past
    include_today = (
        True
        if component["type"] == "datetime"
        else cast(bool, glom(config, "includeToday", default=False))
    )
    config["operator"] = "add" if mode == "future" else "subtract"

    delta = cast(
        DateConstraintDelta,
        {
            "years": 0,
            "months": 0,
            "days": 0 if include_today else 1,
        },
    )
    config["delta"] = delta
    return config


def convert_to_python_type(component_type: str, value: Any) -> date | datetime:
    match [value, component_type]:
        case [datetime(), "date"]:
            assert value.tzinfo is not None, (
                "Expected the input variable to be timezone aware!"
            )
            return timezone.localtime(value=value).date()
        case [date(), "date"]:
            return value
        case [str(), "date"]:
            # attempt to parse it as a date/datetime - could be because the variable
            # was not properly typed and type conversion didn't happen.
            # This can raise ValueError if the string is gibberish.
            return parse_date(value)

        case [datetime(), "datetime"]:
            return value
        case [str(), "datetime"]:
            parsed_value = parse_datetime(value)
            if not parsed_value:
                raise ValueError(f"Could not parse {value} as a datetime")
            return parsed_value

    raise ValueError(
        f"Unexpected type encountered when processing min/max validation for {component_type} component."
    )


def calculate_delta(
    component: DateComponent | DatetimeComponent,
    config: DateConstraintConfiguration,
    data: FormioData,
) -> datetime | None:
    assert config["mode"] == "relativeToVariable"

    base_value = data.get(config["variable"], None)
    if not base_value:
        return

    assert "type" in component
    base_value = convert_to_python_type(component["type"], base_value)

    delta = relativedelta(
        years=cast(int, glom(config, "delta.years", default=None) or 0),
        months=cast(int, glom(config, "delta.months", default=None) or 0),
        days=cast(int, glom(config, "delta.days", default=None) or 0),
    )

    add_or_subtract = glom(config, "operator", default="add")
    func = operator.add if add_or_subtract == "add" else operator.sub
    value = func(base_value, delta)

    if component["type"] == "datetime":
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
