import logging
from typing import Literal, TypedDict

import elasticapm
import requests
from zgw_consumers.client import build_client

from openforms.contrib.hal_client import HALClient

from .api_models.basisprofiel import BasisProfiel
from .models import KVKConfig

logger = logging.getLogger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


def get_client() -> "KVKClient":
    config = KVKConfig.get_solo()
    assert isinstance(config, KVKConfig)
    if not (service := config.service):
        raise NoServiceConfigured("No KVK service configured!")
    return build_client(service, client_factory=KVKClient)


class SearchParams(TypedDict, total=False):
    kvkNummer: str
    rsin: str
    vestigingsnummer: str
    naam: str
    straatnaam: str
    plaats: str
    postcode: str
    huisnummer: int
    huisletter: str
    postbusnummer: int
    huisnummerToevoeging: str
    type: list[str]
    inclusiefInactieveRegistraties: Literal["true", "false"]
    pagina: int  # [1, 1000]
    resultatenPerPagina: int  # [1, 100] - default is 10


class KVKClient(HALClient):
    @elasticapm.capture_span("app.kvk")
    def get_profile(self, kvk_nummer: str) -> BasisProfiel:
        """
        Retrieve the profile of a single entity by chamber of commerce number.

        Docs: https://developers.kvk.nl/apis/basisprofiel
        Swagger: https://developers.kvk.nl/documentation/testing/swagger-basisprofiel-api
        """
        path = f"v1/basisprofielen/{kvk_nummer}"
        try:
            response = self.get(path)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making KVK request", exc_info=exc)
            raise exc

        return response.json()

    @elasticapm.capture_span("app.kvk")
    def get_search_results(self, query_params: SearchParams):
        """
        Perform a search against the KVK zoeken API.

        :arg query_params: must be a non-empty dictionary of query string parameters for
          the actual search.

        Docs: https://developers.kvk.nl/apis/zoeken
        Swagger: https://developers.kvk.nl/documentation/testing/swagger-zoeken-api
        """
        assert query_params, "You must provide at least one query parameter"
        try:
            response = self.get(
                "v2/zoeken",
                params=query_params,  # type: ignore
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making KVK request", exc_info=exc)
            raise exc

        return response.json()
