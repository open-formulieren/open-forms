from datetime import datetime

from django.utils import timezone

import pytz

TIMEZONE_AMS = pytz.timezone("Europe/Amsterdam")


def get_today() -> str:
    now = datetime_in_amsterdam(timezone.now())
    return now.date().isoformat()


def datetime_in_amsterdam(value: datetime) -> datetime:
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)
