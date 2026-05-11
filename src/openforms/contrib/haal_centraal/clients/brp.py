"""
Haal Centraal BRP Personen bevragen API client implementations.

Open Forms supports v2 of the APIs.

Documentation for v2: https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/getting-started
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

import requests
import structlog

from openforms.contrib.client import LoggingClient
from openforms.pre_requests.clients import PreRequestMixin
from openforms.typing import JSONObject

from ..constants import (
    DATE_OF_BIRTH_TYPE_MAPPINGS,
    HC_CHILDREN_ATTRIBUTES,
    HC_DECEASED_ATTRIBUTES,
    HC_PARTNERS_ATTRIBUTES,
    BRPVersions,
)
from ..data import NaturalPersonDetails

logger = structlog.stdlib.get_logger(__name__)


class BRPClient(PreRequestMixin, ABC, LoggingClient):
    def __init__(
        self,
        *args,
        oin_header_name: str = "",
        oin_header_value: str = "",
        doelbinding: str = "",
        verwerking: str = "",
        gebruiker: str = "",
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.headers[oin_header_name] = oin_header_value
        self.headers["x-doelbinding"] = doelbinding
        self.headers["x-verwerking"] = verwerking
        self.headers["x-gebruiker"] = gebruiker

    @abstractmethod
    def find_persons(
        self, bsns: Sequence[str], **kwargs
    ) -> Mapping[str, JSONObject] | None: ...

    @abstractmethod
    def get_family_members(
        self, bsn: str, include_children: bool, include_partner: bool, **kwargs
    ) -> list[NaturalPersonDetails]:
        """
        Look up the partner(s) and/or the children of the person with the given BSN.
        """
        ...

    @abstractmethod
    def make_config_test_request(self) -> None: ...


class V2Client(BRPClient):
    """
    BRP Personen Bevragen 2.0 compatible client.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # requests encodes the json kwarg as utf-8, no extra action needed
        self.headers["Content-Type"] = "application/json; charset=utf-8"

    def find_persons(
        self, bsns: Sequence[str], reraise_errors: bool = False, **kwargs
    ) -> Mapping[str, JSONObject] | None:
        attributes: Sequence[str] = [
            "burgerservicenummer",
            *kwargs.pop("attributes", []),
        ]

        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": bsns,
            "fields": attributes,
        }

        try:
            response = self.post("personen", json=body)
            response.raise_for_status()
        except requests.RequestException as exc:
            if reraise_errors:
                raise exc
            logger.exception("brp_request_failure", exc_info=exc)
            return None

        data = response.json()
        assert isinstance(data, dict)

        if not (persons := data.get("personen", [])):
            logger.debug("person_not_found")
            return None

        return {person["burgerservicenummer"]: person for person in persons}

    def get_family_members(
        self,
        bsn: str,
        include_children: bool,
        include_partner: bool,
        include_deceased: bool = False,
        **kwargs,
    ) -> list[NaturalPersonDetails]:
        fields = []
        if include_children:
            fields += HC_CHILDREN_ATTRIBUTES
        if include_partner:
            fields += HC_PARTNERS_ATTRIBUTES

        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": fields,
        }
        response = self.post("personen", json=body)
        response.raise_for_status()

        data = response.json()
        if not (personen := data.get("personen", [])):
            logger.debug("person_not_found")
            return []

        family_data = []
        if include_children:
            family_data += personen[0]["kinderen"]
        if include_partner:
            family_data += personen[0]["partners"]

        family_members_mappings: dict[str, NaturalPersonDetails] = {}
        for member in family_data:
            if "burgerservicenummer" in member:
                family_members_mappings[member["burgerservicenummer"]] = (
                    NaturalPersonDetails(
                        bsn=member["burgerservicenummer"],
                        first_names=member.get("naam", {}).get("voornamen") or "",
                        initials=member.get("naam", {}).get("voorletters") or "",
                        affixes=member.get("naam", {}).get("voorvoegsel") or "",
                        last_name=member.get("naam", {}).get("geslachtsnaam") or "",
                        date_of_birth=member.get("geboorte", {})
                        .get("datum", {})
                        .get("datum")
                        or "",
                        date_of_birth_precision=DATE_OF_BIRTH_TYPE_MAPPINGS.get(
                            member.get("geboorte", {}).get("datum", {}).get("type")
                        ),
                    )
                )

        if family_members_mappings and not include_deceased:
            bsns_to_check = list(family_members_mappings.keys())
            deceased_persons = self.find_persons(
                bsns_to_check, attributes=HC_DECEASED_ATTRIBUTES
            )
            if deceased_persons:
                for person_bsn, person_data in deceased_persons.items():
                    if "overlijden" in person_data:
                        family_members_mappings.pop(person_bsn)

        return list(family_members_mappings.values())

    def make_config_test_request(self):
        try:
            self.find_persons(
                bsns=["test"],
                attributes=["burgerservicenummer"],
                reraise_errors=True,
            )
        except requests.HTTPError as exc:
            if (response := exc.response) is not None and response.status_code == 400:
                return
            raise exc


CLIENT_CLS_FOR_VERSION: dict[BRPVersions, type[BRPClient]] = {
    BRPVersions.v20: V2Client,
}
