from zgw_consumers_ext.api_client import ServiceClientFactory

from ..models import KadasterApiConfig
from .bag import BAGClient
from .locatieserver import LocatieServerClient


class NoServiceConfigured(RuntimeError):
    pass


def get_locatieserver_client() -> LocatieServerClient:
    config = KadasterApiConfig.get_solo()
    # model field is not nullable because a default is configured
    assert (service := config.search_service)
    service_client_factory = ServiceClientFactory(service)
    return LocatieServerClient.configure_from(service_client_factory)


def get_bag_client() -> BAGClient:
    config = KadasterApiConfig.get_solo()
    if not (service := config.bag_service):
        raise NoServiceConfigured("No BAG service configured!")
    service_client_factory = ServiceClientFactory(service)
    return BAGClient.configure_from(service_client_factory)
