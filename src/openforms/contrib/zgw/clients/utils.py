import datetime
from typing import TypedDict

from django.utils import timezone

import pytz
from ape_pie import APIClient

TIMEZONE_AMS = pytz.timezone("Europe/Amsterdam")


def get_today() -> str:
    now_in_ams = timezone.make_naive(timezone.now(), timezone=TIMEZONE_AMS)
    return now_in_ams.date().isoformat()


def datetime_in_amsterdam(value: datetime) -> datetime:
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)


class PaginatedResponseData(TypedDict):
    count: int
    next: str
    previous: str
    results: list


def pagination_helper(client: APIClient, paginated_data: PaginatedResponseData):
    def _iter(_data):
        for result in _data["results"]:
            yield result
        if next_url := _data["next"]:
            response = client.get(next_url)
            response.raise_for_status()
            data = response.json()
            yield from _iter(data)

    return _iter(paginated_data)
