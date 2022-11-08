import logging
from datetime import datetime

from django.conf import settings

from pytz import timezone

logger = logging.getLogger(__name__)


def format_date_value(raw_value: str) -> str:
    try:
        parsed_datetime = datetime.fromisoformat(raw_value)
    except ValueError:
        try:
            parsed_datetime = datetime.strptime(raw_value, "%Y%m%d")
        except ValueError:
            logger.info("Can't parse date %s, using empty value.", raw_value)
            return ""

    return get_date_in_current_timezone(parsed_datetime)


def get_date_in_current_timezone(value: datetime) -> str:
    current_timezone = timezone(settings.TIME_ZONE)
    return current_timezone.localize(value).isoformat()
