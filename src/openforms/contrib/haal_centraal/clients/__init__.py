from zgw_consumers_ext.api_client import ServiceClientFactory

from ..models import HaalCentraalConfig
from .brp import CLIENT_CLS_FOR_VERSION as BRP_CLIENT_CLS_FOR_VERSION, BRPClient


class NoServiceConfigured(RuntimeError):
    pass


def get_brp_client(**kwargs) -> BRPClient:
    config = HaalCentraalConfig.get_solo()
    if not (service := config.brp_personen_service):
        raise NoServiceConfigured("No BRP service configured!")

    version = config.brp_personen_version
    ClientCls = BRP_CLIENT_CLS_FOR_VERSION.get(version)
    if ClientCls is None:
        raise RuntimeError(
            f"No suitable client class configured for API version {version}"
        )

    service_client_factory = ServiceClientFactory(service)
    return ClientCls.configure_from(service_client_factory, **kwargs)
