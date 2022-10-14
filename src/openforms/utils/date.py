import logging
from datetime import date, datetime

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
