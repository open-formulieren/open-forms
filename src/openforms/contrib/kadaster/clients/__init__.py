from zgw_consumers.client import build_client

from ..models import KadasterApiConfig
from .bag import BAGClient
from .locatieserver import LocatieServerClient


class NoServiceConfigured(RuntimeError):
    pass


def get_locatieserver_client() -> LocatieServerClient:
    config = KadasterApiConfig.get_solo()
    # model field is not nullable because a default is configured
    service = config.search_service
    assert service is not None
    return build_client(service, client_factory=LocatieServerClient)


def get_bag_client() -> BAGClient:
    config = KadasterApiConfig.get_solo()
    if not (service := config.bag_service):
        raise NoServiceConfigured("No BAG service configured!")
    return build_client(service, client_factory=BAGClient)
