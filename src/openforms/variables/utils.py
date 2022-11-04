from datetime import date, datetime, time
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time

from openforms.typing import JSONObject, JSONValue
from openforms.utils.date import format_date_value


def check_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError:
        datetime.fromisoformat(value)
    return value


def check_time(value: str) -> str:
    try:
        time.fromisoformat(value)
    except ValueError:
        datetime.fromisoformat(value)
    return value


def check_initial_value(initial_value: JSONObject, data_type: str) -> JSONObject:
    from .constants import CHECK_VARIABLE_TYPE, DEFAULT_INITIAL_VALUE

    try:
        return CHECK_VARIABLE_TYPE[data_type](initial_value)
    except (ValueError, TypeError):
        return DEFAULT_INITIAL_VALUE[data_type]


def variable_value_to_python(value: JSONValue, data_type: str) -> Any:
    """Deserialize the value into the appropriate python type.

    TODO: for dates/datetimes, we rely on our django settings for timezone
    information, however - formio submission does send the user's configured
    timezone as metadata, which we can store on the submission/submission step
    to correctly interpret the data. For the time being, this is not needed yet
    as we focus on NL first.
    """
    from .constants import FormVariableDataTypes

    if value is None:
        return None

    # we expect JSON types to have been properly stored (and thus not as string!)
    if data_type in (
        FormVariableDataTypes.string,
        FormVariableDataTypes.boolean,
        FormVariableDataTypes.object,
        FormVariableDataTypes.int,
        FormVariableDataTypes.float,
        FormVariableDataTypes.array,
    ):
        return value

    # TODO what about an array of datetimes?
    if value and data_type == FormVariableDataTypes.datetime:
        date = format_date_value(value)
        naive_date = parse_date(date)
        if naive_date is not None:
            aware_date = timezone.make_aware(datetime.combine(naive_date, time.min))
            return aware_date

        # not a date - try parsing a datetime then
        maybe_naive_datetime = parse_datetime(value)
        if maybe_naive_datetime is not None:
            if timezone.is_aware(maybe_naive_datetime):
                return maybe_naive_datetime
            return timezone.make_aware(maybe_naive_datetime)

        raise ValueError(f"Could not parse date/datetime '{value}'")  # pragma: nocover

    if value and data_type == FormVariableDataTypes.time:
        value = parse_time(value)
        if value is not None:
            return value
        raise ValueError(f"Could not parse time '{value}'")  # pragma: nocover

    return value
