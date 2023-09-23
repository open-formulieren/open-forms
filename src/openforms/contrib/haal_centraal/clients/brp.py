"""
Haal Centraal BRP Personen bevragen API client implementations.

Open Forms supports v1 and v2 of the APIs.

Documentation for v2: https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/getting-started
"""
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import requests

from openforms.contrib.hal_client import HALClient
from openforms.pre_requests.clients import PreRequestClientContext
from openforms.typing import JSONObject

from ..constants import BRPVersions

logger = logging.getLogger(__name__)

# DATA MODEL DEFINITIONS


@dataclass
class Name:
    voornamen: str
    voorvoegsel: str
    geslachtsnaam: str


@dataclass
class Person:
    bsn: str
    name: Name


# CLIENT IMPLEMENTATIONS


class BRPClient(HALClient, ABC):
    def __init__(self, *args, context: PreRequestClientContext | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: check how we can make the context work with pre-requests & if we can
        # namespace this thing better
        self.context = context

    @abstractmethod
    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:  # pragma: no cover
        ...

    @abstractmethod
    def get_children(self, bsn: str) -> list[Person]:  # pragma: no cover
        """
        Look up the children of the person with the given BSN.
        """
        ...

    @abstractmethod
    def make_config_test_request(self) -> None:  # pragma: no cover
        ...


class V1Client(BRPClient):
    """
    BRP Personen Bevragen 1.3 compatible client.
    """

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        try:
            response = self.get(f"ingeschrevenpersonen/{bsn}")
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making request", exc_info=exc)
            return None

        return response.json()

    def get_children(self, bsn: str) -> list[Person]:
        # FIXME: I suspect that Open Personen's API spec is wrong here, let's see if
        # we can find an old V1 API spec.
        response = self.get(f"ingeschrevenpersonen/{bsn}/kinderen")
        response.raise_for_status()
        response_data = response.json()["_embedded"]

        persons = []
        for kind in response_data["kinderen"]:
            name_data = kind["_embedded"]["naam"]
            person = Person(
                bsn=kind["burgerservicenummer"],
                name=Name(
                    voornamen=name_data["voornamen"],
                    voorvoegsel=name_data["voorvoegsel"],
                    geslachtsnaam=name_data["geslachtsnaam"],
                ),
            )
            persons.append(person)
        return persons

    def make_config_test_request(self):
        # expected to 404
        response = self.get("test")
        if response.status_code != 404:
            response.raise_for_status()


class V2Client(BRPClient):
    """
    BRP Personen Bevragen 2.0 compatible client.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. they don't expect hal+json as request content-type (!)
        # 2. requests encodes the json kwarg as utf-8, no extra action needed
        self.headers["Content-Type"] = "application/json; charset=utf-8"

    def find_person(
        self, bsn: str, reraise_errors: bool = False, **kwargs
    ) -> JSONObject | None:
        attributes: Sequence[str] = kwargs.pop("attributes")
        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": attributes,
        }

        try:
            response = self.post("personen", json=body)
            response.raise_for_status()
        except requests.RequestException as exc:
            if reraise_errors:
                raise exc
            logger.exception("exception while making request", exc_info=exc)
            return None

        data = response.json()
        assert isinstance(data, dict)

        if not (personen := data.get("personen", [])):
            logger.debug("Person not found")
            return None

        return personen[0]

    def get_children(self, bsn: str) -> list[Person]:
        fields = ["kinderen.burgerservicenummer", "kinderen.naam"]
        raise NotImplementedError

    def make_config_test_request(self):
        try:
            self.find_person(
                bsn="test",
                attributes=["burgerservicenummer"],
                reraise_errors=True,
            )
        except requests.HTTPError as exc:
            if (response := exc.response) is not None and response.status_code == 400:
                return
            raise exc


CLIENT_CLS_FOR_VERSION: dict[BRPVersions, type[BRPClient]] = {
    BRPVersions.v13: V1Client,
    BRPVersions.v20: V2Client,
}
