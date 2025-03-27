from datetime import datetime, timedelta

from django.utils import timezone


def check_expired_or_near_expiry(einddatum: str) -> bool:
    parsed_datetime = datetime.fromisoformat(einddatum)
    in_seven_days = timezone.now() + timedelta(days=7)
    return not (parsed_datetime > in_seven_days)
