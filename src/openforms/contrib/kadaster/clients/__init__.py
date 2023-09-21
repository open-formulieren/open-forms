from zgw_consumers_ext.api_client import ServiceClientFactory

from ..models import KadasterApiConfig
from .locatieserver import LocatieServerClient


def get_locatieserver_client() -> LocatieServerClient:
    config = KadasterApiConfig.get_solo()
    assert isinstance(config, KadasterApiConfig)
    # model field is not nullable because a default is configured
    assert (service := config.search_service)
    service_client_factory = ServiceClientFactory(service)
    return LocatieServerClient.configure_from(service_client_factory)
