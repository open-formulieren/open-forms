import logging
from typing import TypedDict

import requests

from openforms.contrib.hal_client import HALClient
from zgw_consumers_ext.api_client import ServiceClientFactory

from .models import BRKConfig

logger = logging.getLogger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


def get_client() -> "BRKClient":
    config = BRKConfig.get_solo()
    assert isinstance(config, BRKConfig)
    if not (service := config.service):
        raise NoServiceConfigured("No KVK service configured!")
    service_client_factory = ServiceClientFactory(service)
    return BRKClient.configure_from(service_client_factory)


class SearchParams(TypedDict, total=False):
    postcode: str
    huisnummer: str
    huisletter: str
    huisnummertoevoeging: str


class BRKClient(HALClient):
    def get_cadastrals_by_address(self, query_params: SearchParams):
        """
        Search for cadastrals by querying for a specifc address.

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
        Search for commercial titleholders of a cadastral immovable property.

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
