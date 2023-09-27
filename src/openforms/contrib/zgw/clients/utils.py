from django.utils import timezone

import pytz

TIMEZONE_AMS = pytz.timezone("Europe/Amsterdam")


def get_today() -> str:
    now_in_ams = timezone.make_naive(timezone.now(), timezone=TIMEZONE_AMS)
    return now_in_ams.date().isoformat()
