from datetime import datetime, timedelta

from django.utils import timezone


def check_expired_or_near_expiry(einddatum: str) -> bool:
    parsed_datetime = datetime.fromisoformat(einddatum)
    return (
        timezone.now() <= parsed_datetime <= timezone.now() + timedelta(days=7)
    ) or (parsed_datetime < timezone.now())
