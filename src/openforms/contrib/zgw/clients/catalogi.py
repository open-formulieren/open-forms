from datetime import date
from operator import itemgetter
from typing import Callable, Iterator, NotRequired, TypeAlias, TypedDict

from requests import Response
from zgw_consumers.nlx import NLXClient

from openforms.utils.api_clients import PaginatedResponseData, pagination_helper

from ..exceptions import StandardViolation


def noop_matcher(roltypen: list) -> list:
    return roltypen


def omschrijving_matcher(omschrijving: str):
    def match_omschrijving(roltypen: list) -> list:
        matches = []
        for roltype in roltypen:
            if roltype.get("omschrijving") == omschrijving:
                matches.append(roltype)
        return matches

    return match_omschrijving


class Catalogus(TypedDict):
    # there are more attributes, but we currently don't use them. See the Catalogi
    # API spec
    url: str
    domein: str
    rsin: str
    naam: NotRequired[str]  # not present in older versions
    informatieobjecttypen: list[str]


class InformatieObjectType(TypedDict):
    # there are more attributes, but we currently don't use them. See the Catalogi
    # API spec
    url: str
    catalogus: str  # URL pointer to the catalogue
    omschrijving: str
    beginGeldigheid: str  # ISO 8601 date string
    eindeGeldigheid: NotRequired[str | None]  # ISO 8601 date string or empty
    concept: NotRequired[bool]


CatalogiAPIVersion: TypeAlias = tuple[
    int,  # major
    int,  # minor
    int,  # patch
]


class CatalogiClient(NLXClient):
    _api_version: CatalogiAPIVersion | None = None

    @property
    def api_version(self) -> CatalogiAPIVersion:
        if self._api_version is None:
            # hit a known endpoint and parse the response headers. VRSN is just a made
            # up domain to limit the result set, hopefully it's even entirely empty.
            response = self.get("catalogussen", params={"domein": "VRSN"})
            self._api_version = self._determine_api_version(response)
        return self._api_version

    def _determine_api_version(self, response: Response) -> CatalogiAPIVersion:
        try:
            version = response.headers["API-version"]
        except KeyError as exc:
            raise StandardViolation(
                "API-version is a required response header."
            ) from exc
        try:
            major, minor, patch = [int(bit) for bit in version.split(".")]
        except ValueError as exc:
            raise StandardViolation("API-version must follow semver format.") from exc
        return (major, minor, patch)

    def request(self, *args, **kwargs):
        response = super().request(*args, **kwargs)
        if not self._api_version:
            self._api_version = self._determine_api_version(response)
        return response

    def get_all_catalogi(self) -> Iterator[dict]:
        """
        List all available catalogi, consuming pagination if relevant.
        """
        response = self.get("catalogussen")
        response.raise_for_status()
        data = response.json()
        yield from pagination_helper(self, data)

    def find_catalogus(self, *, domain: str, rsin: str) -> Catalogus | None:
        """
        Look up the catalogus uniquely identified by domain and rsin.

        If no match is found, ``None`` is returned.
        """
        response = self.get("catalogussen", params={"domein": domain, "rsin": rsin})
        response.raise_for_status()
        data: PaginatedResponseData[Catalogus] = response.json()

        if (num_results := len(data["results"])) > 1:
            raise StandardViolation(
                "Combination of domain + rsin must be unique according to the standard."
            )
        if num_results == 0:
            return None
        return data["results"][0]

    def get_all_informatieobjecttypen(self, *, catalogus: str = "") -> Iterator[dict]:
        """List all informatieobjecttypen.

        :arg catalogus: the catalogus URL the informatieobjecttypen should belong to.
        """
        params = {}
        if catalogus:
            params["catalogus"] = catalogus
        response = self.get("informatieobjecttypen", params=params)
        response.raise_for_status()
        data = response.json()
        yield from pagination_helper(self, data)

    def find_informatieobjecttypen(
        self,
        *,
        catalogus: str,
        description: str,
        valid_on: date | None = None,
    ) -> list[InformatieObjectType] | None:
        """
        Look up an informatieobjecttype within the specified catalogue.

        The description is unique within a catalogue, but multiple versions may exist.
        If no results are found, ``None`` is returned.
        """
        _supports_filtering_valid_on = self.api_version >= (1, 2, 0)

        params = {
            "catalogus": catalogus,
            "omschrijving": description,
        }

        # datumGeldigheid was added in v1.2.0 of the APIs & the APIs reject query string
        # parameters that are unkonwn, so we can not just optmistically send it :(
        if valid_on and _supports_filtering_valid_on:
            params["datumGeldigheid"] = valid_on.isoformat()

        response = self.get("informatieobjecttypen", params=params)
        response.raise_for_status()
        data: PaginatedResponseData[InformatieObjectType] = response.json()
        if data["count"] == 0:
            return None

        all_versions = sorted(
            list(pagination_helper(self, data)),
            key=itemgetter("beginGeldigheid"),
        )

        # otherwise do the filtering manually
        if valid_on and not _supports_filtering_valid_on:
            date_str = valid_on.isoformat()
            all_versions = [
                version
                for version in all_versions
                if version["beginGeldigheid"] <= date_str
                if (end := version.get("eindeGeldigheid")) is None or end > date_str
            ]
        elif (
            valid_on and _supports_filtering_valid_on and (num := len(all_versions)) > 1
        ):
            raise StandardViolation(
                f"Got {num} document type versions within a catalogue with description "
                f"'{description}'. Version (date) ranges may not overlap."
            )

        return all_versions

    def list_statustypen(self, zaaktype: str) -> list[dict]:
        query = {"zaaktype": zaaktype}

        response = self.get("statustypen", params=query)
        response.raise_for_status()

        results = response.json()["results"]
        return results

    def list_roltypen(
        self,
        zaaktype: str,
        omschrijving_generiek: str = "",
        matcher: Callable[[list], list] = noop_matcher,
    ):
        query = {"zaaktype": zaaktype}
        if omschrijving_generiek:
            query["omschrijvingGeneriek"] = omschrijving_generiek

        response = self.get("roltypen", params=query)
        response.raise_for_status()

        results = response.json()["results"]
        return matcher(results)

    def list_eigenschappen(self, zaaktype: str) -> list[dict]:
        query = {"zaaktype": zaaktype}

        response = self.get("eigenschappen", params=query)
        response.raise_for_status()
        data = response.json()
        all_data = pagination_helper(self, data)
        return list(all_data)
