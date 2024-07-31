from typing import Callable, Iterator, NotRequired, TypedDict

from zgw_consumers.nlx import NLXClient

from openforms.utils.api_clients import PaginatedResponseData, pagination_helper


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
    domein: str
    rsin: str
    naam: NotRequired[str]  # not present in older versions
    informatieobjecttypen: list[str]


class CatalogiClient(NLXClient):
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
            raise RuntimeError(
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
