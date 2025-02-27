from functools import partial
from typing import Any, TypedDict

from django.core.cache import cache

from ape_pie import APIClient
from zgw_consumers.service import pagination_helper

REFERENTIELIJSTEN_LOOKUP_CACHE_TIMEOUT = 5 * 60


class TabelItem(TypedDict):
    code: str
    naam: str
    begindatumGeldigheid: str  # ISO 8601 datetime string
    einddatumGeldigheid: str | None  # ISO 8601 datetime string
    aanvullendeGegevens: Any


class Beheerder(TypedDict):
    naam: str
    email: str
    afdeling: str
    organisatie: str


class Tabel(TypedDict):
    code: str
    naam: str
    beheerder: Beheerder
    einddatumGeldigheid: str | None  # ISO 8601 datetime string


class ReferentielijstenClient(APIClient):
    def get_tabellen(self) -> list[Tabel]:
        response = self.get("tabellen", timeout=10)
        response.raise_for_status()
        data = response.json()
        all_data = list(pagination_helper(self, data))
        return all_data

    def get_items_for_tabel(self, code: str) -> list[TabelItem]:
        response = self.get("items", params={"tabel__code": code}, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_data = list(pagination_helper(self, data))
        return all_data

    def get_items_for_tabel_cached(self, code: str) -> list[TabelItem]:
        result = cache.get_or_set(
            key=f"referentielijsten|get_items_for_tabel|code:{code}",
            default=partial(self.get_items_for_tabel, code),
            timeout=REFERENTIELIJSTEN_LOOKUP_CACHE_TIMEOUT,
        )
        assert result is not None
        return result
