import logging
from datetime import date, datetime, time

from django.utils import timezone
from django.utils.dateparse import (
    parse_datetime as _parse_datetime,
    parse_time as _parse_time,
)

logger = logging.getLogger(__name__)


def format_date_value(date_value: str) -> str:
    try:
        parsed_date = date.fromisoformat(date_value)
    except ValueError:
        try:
            parsed_date = datetime.strptime(date_value, "%Y%m%d").date()
        except ValueError:
            logger.info("Can't parse date %s, using empty value.", date_value)
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


def parse_datetime(value: str) -> str | datetime:
    try:
        return _parse_datetime(value)
    except ValueError:
        logger.info("Can't parse datetime '%s', using empty string.", value)
        return ""


def parse_time(value: str) -> str | time:
    try:
        return _parse_time(value)
    except ValueError:
        logger.info("Can't parse time '%s', using empty string.", value)
        return ""
