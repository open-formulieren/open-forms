import operator
from datetime import datetime, time
from typing import Literal, Optional, TypedDict, Union, cast

from django.utils import timezone

from dateutil.relativedelta import relativedelta
from glom import assign, glom

from openforms.typing import DataMapping

from ..typing import Component

NOW_VARIABLE = "now"


class DateConstraintDelta(TypedDict):
    years: Optional[int]
    months: Optional[int]
    days: Optional[int]


class DateConstraintConfiguration(TypedDict):
    mode: Literal["fixedValue", "future", "past", "relativeToVariable"]
    includeToday: Optional[bool]
    variable: Optional[str]
    delta: Optional[DateConstraintDelta]
    operator: Optional[Literal["add", "subtract"]]


class OpenFormsConfig(TypedDict):
    minDate: Optional[DateConstraintConfiguration]
    maxDate: Optional[DateConstraintConfiguration]


class DatePickerConfig(TypedDict):
    minDate: Optional[str]
    maxDate: Optional[str]


class FormioDateComponent(Component):
    openForms: Optional[OpenFormsConfig]
    datePicker: Optional[DatePickerConfig]


def mutate(component: FormioDateComponent, data: DataMapping) -> None:
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

        config = normalize_config(config)
        value = calculate_delta(config, data)
        if value and isinstance(value, datetime):
            value = value.isoformat()
        assign(component, f"datePicker.{key}", value, missing=dict)


def normalize_config(
    config: DateConstraintConfiguration,
) -> DateConstraintConfiguration:
    mode = config["mode"]
    assert mode in ("future", "past", "relativeToVariable")
    if mode == "relativeToVariable":
        return config

    # mode is now future or past -> convert that to a relative delta config
    config["mode"] = "relativeToVariable"
    config["variable"] = NOW_VARIABLE
    include_today = cast(bool, glom(config, "includeToday", default=False))
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


def calculate_delta(
    config: DateConstraintConfiguration,
    data: DataMapping,
) -> Optional[datetime]:
    assert config["mode"] == "relativeToVariable"

    base_value = cast(
        Optional[Union[datetime, str]],
        glom(data, config["variable"], default=None),
    )
    # can't do calculations on values that don't exist or are empty
    if not base_value:
        return None

    # if it's not empty-ish, it's a datetime
    base_value = cast(datetime, base_value)

    assert (
        base_value.tzinfo is not None
    ), "Expected the input variable to be timezone aware!"
    base_date = timezone.localtime(value=base_value).date()

    delta = relativedelta(
        years=cast(int, glom(config, "delta.years", default=None) or 0),
        months=cast(int, glom(config, "delta.months", default=None) or 0),
        days=cast(int, glom(config, "delta.days", default=None) or 0),
    )

    add_or_subtract = glom(config, "operator", default="add")
    func = operator.add if add_or_subtract == "add" else operator.sub
    value = func(base_date, delta)

    # convert to datetime at midnight for the date in the local timezone
    naive_value = datetime.combine(value, time.min)
    return timezone.make_aware(naive_value)
