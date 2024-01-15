import logging
from typing import TypedDict

import requests
from ape_pie.client import APIClient
from typing_extensions import NotRequired

from zgw_consumers_ext.api_client import ServiceClientFactory

from .models import BRKConfig

logger = logging.getLogger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


def get_client() -> "BRKClient":
    config = BRKConfig.get_solo()
    if not (service := config.service):
        raise NoServiceConfigured("No BRK service configured!")
    service_client_factory = ServiceClientFactory(service)
    return BRKClient.configure_from(service_client_factory)


class SearchParams(TypedDict):
    postcode: str
    huisnummer: str
    huisletter: NotRequired[str]
    huisnummertoevoeging: NotRequired[str]


class BRKClient(APIClient):
    def get_real_estate_by_address(self, query_params: SearchParams):
        """
        Search for real estate by querying for a specific address.

        API docs: https://vng-realisatie.github.io/Haal-Centraal-BRK-bevragen/swagger-ui-2.0#/Kadastraal%20Onroerende%20Zaken/GetKadastraalOnroerendeZaken
        """
        assert query_params, "You must provide at least one query parameter"

        try:
            response = self.get(
                "kadastraalonroerendezaken",
                params=query_params,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making BRK request", exc_info=exc)
            raise exc

        return response.json()

    def get_cadastral_titleholders_by_cadastral_id(self, cadastral_id: str):
        """
        Look up the rightholders of a property (e.g. a house) in the Dutch cadastre.

        API docs: https://vng-realisatie.github.io/Haal-Centraal-BRK-bevragen/swagger-ui-2.0#/Zakelijke%20Gerechtigden/GetZakelijkGerechtigden
        """
        try:
            response = self.get(
                f"kadastraalonroerendezaken/{cadastral_id}/zakelijkgerechtigden",
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making BRK request", exc_info=exc)
            raise exc

        return response.json()
