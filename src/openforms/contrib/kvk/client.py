import logging

import elasticapm
import requests
from zds_client import ClientError

from openforms.contrib.hal_client import HALClient
from zgw_consumers_ext.api_client import ServiceClientFactory

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
    service_client_factory = ServiceClientFactory(service)
    return KVKClient.configure_from(service_client_factory)


class KVKClient(HALClient):
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


class KVKSearchClient:
    # https://api.kvk.nl/api/v1/zoeken?x=y
    # https://api.kvk.nl/test/api/v1/zoeken?x=y
    # docs: https://developers.kvk.nl/apis/zoeken

    @elasticapm.capture_span("app.kvk")
    def query(self, **query_params):
        config = KVKConfig.get_solo()
        if not config.service:
            logger.warning("no service defined for KvK client")
            raise KVKClientError("no service defined")

        client = config.service.build_client()

        try:
            results = client.operation(
                "getResults",
                method="GET",
                data=None,
                request_kwargs=dict(
                    params=query_params,
                ),
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making KVK request", exc_info=e)
            raise e
        else:
            return results
