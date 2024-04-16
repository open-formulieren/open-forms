import logging
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.dateparse import (
    parse_datetime as _parse_datetime,
    parse_time as _parse_time,
)

logger = logging.getLogger(__name__)


TIMEZONE_AMS = ZoneInfo("Europe/Amsterdam")


def format_date_value(date_value: str) -> str:
    try:
        parsed_date = date.fromisoformat(date_value)
    except ValueError:
        try:
            parsed_date = datetime.strptime(date_value, "%Y%m%d").date()
        except ValueError:
            logger.info(
                "Can't format date '%s', falling back to an empty string.", date_value
            )
            return ""

    return parsed_date.isoformat()


def parse_date(value: str) -> date:
    """
    Attempt to parse the input as a date.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass  # fall through to check for datetime

    dt = datetime.fromisoformat(value)
    assert dt.tzinfo is not None, "Expected the input variable to be timezone aware!"
    return timezone.localtime(value=dt).date()


def parse_datetime(value: str) -> None | datetime:
    try:
        datetime_value = _parse_datetime(value)
    except ValueError:
        logger.info("Can't parse datetime '%s', falling back to 'None' instead.", value)
        return

    if datetime_value is None:
        logger.info(
            "Badly formatted datetime '%s', falling back to 'None' instead.", value
        )
        return

    return datetime_value


def parse_time(value: str) -> None | time:
    try:
        time_value = _parse_time(value)
    except ValueError:
        logger.info("Invalid time '%s', falling back to 'None' instead.", value)
        return

    if time_value is None:
        logger.info("Badly formatted time '%s', falling back to 'None' instead.", value)
        return

    return time_value


def datetime_in_amsterdam(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return value
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)


def get_today() -> str:
    now = datetime_in_amsterdam(timezone.now())
    return now.date().isoformat()
