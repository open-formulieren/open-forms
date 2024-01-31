from typing import Callable

from zgw_consumers.nlx import NLXClient

from .utils import pagination_helper


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


class CatalogiClient(NLXClient):
    def get_all_catalogi(self) -> list[dict]:
        """
        List all available catalogi, consuming pagination if relevant.
        """
        response = self.get("catalogussen")
        response.raise_for_status()
        data = response.json()
        all_data = pagination_helper(self, data)
        return list(all_data)

    def get_all_informatieobjecttypen(self) -> list[dict]:
        response = self.get("informatieobjecttypen")
        response.raise_for_status()
        data = response.json()
        all_data = pagination_helper(self, data)
        return list(all_data)

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
