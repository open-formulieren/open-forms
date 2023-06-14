import logging
from typing import Iterable, Protocol

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.client import ZGWClient

from openforms.typing import JSONObject

logger = logging.getLogger(__name__)


class HaalCentraalClient(Protocol):
    def __init__(self, service_client: ZGWClient):
        ...

    def find_person(self, bsn: str, **kwargs) -> JSONObject:
        ...


class HaalCentraalV1Client:
    """
    Haal Centraal 1.3 compatible client.
    """

    def __init__(self, service_client: ZGWClient):
        self.service_client = service_client

    def find_person(self, bsn: str, *args, **kwargs) -> JSONObject:
        try:
            data = self.service_client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=bsn,
                url=f"ingeschrevenpersonen/{bsn}",
                request_kwargs={
                    "headers": {"Accept": "application/hal+json"},
                },
            )
        except RequestException as e:
            logger.exception("exception while making request", exc_info=e)
            return
        except ClientError as e:
            logger.exception("exception while making request", exc_info=e)
            return

        return data


class HaalCentraalV2Client:
    """
    Haal Centraal 2.0 compatible client.
    """

    def __init__(self, service_client: ZGWClient):
        self.service_client = service_client

    def find_person(self, bsn: str, attributes: Iterable[str]) -> JSONObject:
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
        except RequestException as e:
            logger.exception("exception while making request", exc_info=e)
            return
        except ClientError as e:
            logger.exception("exception while making request", exc_info=e)
            return

        if data.get("personen"):
            return data["personen"][0]
        return data
