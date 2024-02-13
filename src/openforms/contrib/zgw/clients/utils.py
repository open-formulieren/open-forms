from django.utils import timezone

from openforms.utils.date import datetime_in_amsterdam


def get_today() -> str:
    now = datetime_in_amsterdam(timezone.now())
    return now.date().isoformat()
