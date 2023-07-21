import logging
from collections.abc import Sequence
from typing import Protocol

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.client import ZGWClient

from openforms.typing import JSONObject

from .constants import AttributesV2

logger = logging.getLogger(__name__)


class HaalCentraalClient(Protocol):
    def __init__(self, service_client: ZGWClient):  # pragma: no cover
        ...

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:  # pragma: no cover
        ...

    def make_config_test_request(self) -> None:  # pragma: no cover
        ...


class HaalCentraalV1Client:
    """
    Haal Centraal 1.3 compatible client.
    """

    def __init__(self, service_client: ZGWClient):
        self.service_client = service_client

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        try:
            data = self.service_client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=bsn,
                url=f"ingeschrevenpersonen/{bsn}",
                request_kwargs={
                    "headers": {"Accept": "application/hal+json"},
                },
            )
        except (ClientError, RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        return data

    def make_config_test_request(self):
        try:
            self.service_client.retrieve("test", "test")
        except ClientError as e:
            if e.args[0].get("status") == 404:
                return
            raise


class HaalCentraalV2Client:
    """
    Haal Centraal 2.0 compatible client.
    """

    def __init__(self, service_client: ZGWClient):
        self.service_client = service_client

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        attributes: Sequence[str] = kwargs.pop("attributes")
        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": attributes,
        }

        try:
            data = self.service_client.operation(
                "Personen",
                data=body,
                url="personen",
                request_kwargs={
                    "headers": {"Content-Type": "application/json; charset=utf-8"}
                },
            )
            assert isinstance(data, dict)
        except (ClientError, RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        if not data.get("personen"):
            logger.debug("Personen not found")
            return

        return data["personen"][0]

    def make_config_test_request(self):
        try:
            self.service_client.operation(
                "test",
                data={
                    "type": "RaadpleegMetBurgerservicenummer",
                    "burgerservicenummer": ["test"],
                    "fields": [AttributesV2.burgerservicenummer],
                },
                url="test",
                request_kwargs={
                    "headers": {"Content-Type": "application/json; charset=utf-8"}
                },
            )
        except ClientError as e:
            if e.args[0].get("status") == 400:
                return
            raise
