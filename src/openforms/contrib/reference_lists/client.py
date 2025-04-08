from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial

from django.core.cache import cache
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import get_language

from ape_pie import APIClient
from zgw_consumers.service import pagination_helper

from .typing import APITable, APITableItem

REFERENCE_LISTS_LOOKUP_CACHE_TIMEOUT = 5 * 60
NEARLY_EXPIRED_DAYS = 7


class EndDateMixin:
    expires_on: datetime | None

    @cached_property
    def is_expired(self) -> bool:
        if self.expires_on is None:
            return False
        return self.expires_on <= timezone.now()

    @cached_property
    def is_nearly_expired(self) -> bool:
        if self.expires_on is None:
            return False
        return self.expires_on <= (timezone.now() + timedelta(days=NEARLY_EXPIRED_DAYS))


@dataclass
class TableItem(EndDateMixin):
    code: str
    name: str
    expires_on: datetime | None = None  # from ISO 8601 datetime string


@dataclass
class Table(EndDateMixin):
    code: str
    name: str
    expires_on: datetime | None = None  # from ISO 8601 datetime string


class ReferenceListsClient(APIClient):

    def get_table(self, code: str) -> Table | None:
        response = self.get("tabellen", params={"code": code})
        response.raise_for_status()
        data = response.json()
        all_data: list[APITable] = list(pagination_helper(self, data))
        if not all_data:
            return

        # The API always returns a list and code is a unique field in the model, so there
        # will be one item in the list
        return Table(
            code=all_data[0]["code"],
            name=all_data[0]["naam"],
            expires_on=(
                None
                if (datestr := all_data[0].get("einddatumGeldigheid")) is None
                else datetime.fromisoformat(datestr)
            ),
        )

    def get_all_tables(self) -> list[Table]:
        response = self.get("tabellen")
        response.raise_for_status()
        data = response.json()
        all_data: list[APITable] = list(pagination_helper(self, data))
        return [
            Table(
                code=record["code"],
                name=record["naam"],
                expires_on=(
                    None
                    if (datestr := record.get("einddatumGeldigheid")) is None
                    else datetime.fromisoformat(datestr)
                ),
            )
            for record in all_data
        ]

    def get_items_for_table(self, code: str, current_language: str) -> list[TableItem]:
        response = self.get(
            "items",
            params={"tabel__code": code},
            headers={"Accept-Language": current_language},
        )
        response.raise_for_status()
        data = response.json()
        all_data: list[APITableItem] = list(pagination_helper(self, data))
        return [
            TableItem(
                code=record["code"],
                name=record["naam"],
                expires_on=(
                    None
                    if (datestr := record.get("einddatumGeldigheid")) is None
                    else datetime.fromisoformat(datestr)
                ),
            )
            for record in all_data
        ]

    def get_items_for_table_cached(self, code: str) -> list[TableItem]:
        current_language = get_language()
        result = cache.get_or_set(
            key=f"reference_lists|get_items_for_table|code:{code}|language:{current_language}",
            default=partial(self.get_items_for_table, code, current_language),
            timeout=REFERENCE_LISTS_LOOKUP_CACHE_TIMEOUT,
        )
        assert result is not None
        return result
