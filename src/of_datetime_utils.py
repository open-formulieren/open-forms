"""
Provide utilities to work with (local) dates and times.

The functionality in this module is used in the ``openforms``, ``stuf`` and ``formio``
packages, and there's no clear owner. To separate boundaries between packages, this is
lifted in a shared utilities module.

It *does* depend on django, but should do so in loosely coupled way. Ideally, this would
be pure Python, but practicality and purity require a compromise here.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

TIMEZONE_AMS = ZoneInfo("Europe/Amsterdam")


def datetime_in_amsterdam(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return value
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)


def get_today() -> date:
    now = datetime_in_amsterdam(timezone.now())
    return now.date()
