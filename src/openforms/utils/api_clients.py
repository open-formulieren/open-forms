from collections.abc import Iterator
from typing import TypedDict

from ape_pie import APIClient


class PaginatedResponseData[T](TypedDict):
    count: int
    next: str
    previous: str
    results: list[T]


def pagination_helper[T](
    client: APIClient, paginated_data: PaginatedResponseData[T]
) -> Iterator[T]:
    """A helper to iterate over the paginated data of an API response.

    This helper is meant to work with Django REST Framework pagination style, where responses contain:
    - a ``next`` key, to fetch the next results.
    - a ``results`` key, mapping to a list of API specific data.
    """

    def _iter(_data: PaginatedResponseData[T]) -> Iterator[T]:
        yield from _data["results"]
        if next_url := _data["next"]:
            response = client.get(next_url)
            response.raise_for_status()
            data = response.json()
            yield from _iter(data)

    return _iter(paginated_data)
