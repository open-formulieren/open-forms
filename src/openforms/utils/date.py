from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.dateparse import (
    parse_datetime as _parse_datetime,
    parse_time as _parse_time,
)

import structlog

logger = structlog.stdlib.get_logger(__name__)


TIMEZONE_AMS = ZoneInfo("Europe/Amsterdam")


def format_date_value(date_value: str | date | None) -> str:
    if date_value is None:
        return ""
    if isinstance(date_value, date):
        return date_value.isoformat()

    try:
        parsed_date = date.fromisoformat(date_value)
    except ValueError:
        try:
            parsed_date = datetime.strptime(date_value, "%Y%m%d").date()
        except ValueError as exc:
            logger.info(
                "date_formatting_error", value=date_value, fallback="", exc_inf=exc
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
    log = logger.bind(value=value, fallback=None)
    try:
        datetime_value = _parse_datetime(value)
    except ValueError as exc:
        log.info("datetime_parse_error", exc_info=exc)
        return

    if datetime_value is None:
        log.info("bad_datetime_format")
        return

    return datetime_value


def parse_time(value: str) -> None | time:
    log = logger.bind(value=value, fallback=None)
    try:
        time_value = _parse_time(value)
    except ValueError as exc:
        log.info("time_parse_error", exc_info=exc)
        return

    if time_value is None:
        log.info("bad_time_format")
        return

    return time_value


def datetime_in_amsterdam(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return value
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)


def get_today() -> date:
    now = datetime_in_amsterdam(timezone.now())
    return now.date()
