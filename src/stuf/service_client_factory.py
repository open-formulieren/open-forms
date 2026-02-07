from dataclasses import dataclass
from typing import Any

from soap.constants import EndpointSecurity

from .constants import EndpointType
from .models import StufService
from .stuf import InvolvedParty, StuurGegevens, WSSecurity


@dataclass
class ServiceClientFactory:
    service: StufService

    def get_client_base_url(self) -> str:
        # while we have different endpoint types, the attached soap service itself also
        # defines a (potentially empty!) base URL which is normally used as fallback.
        return self.service.soap_service.url

    def get_client_session_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "verify": self.service.get_verify(),
            "cert": self.service.get_cert(),
            "auth": self.service.get_auth(),
            "timeout": self.service.get_timeout(),
        }
        return kwargs


def get_client_init_kwargs(service: StufService):
    # pass the endpoint types map
    endpoints = {
        endpoint_type: service.get_endpoint(endpoint_type)
        for endpoint_type in EndpointType
    }
    wss_security = WSSecurity(
        use_wss=service.soap_service.endpoint_security
        in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth],
        wss_username=service.soap_service.user,
        wss_password=service.soap_service.password,
    )
    stuurgegevens = StuurGegevens(
        zender=InvolvedParty.from_service_configuration(service, "zender"),
        ontvanger=InvolvedParty.from_service_configuration(service, "ontvanger"),
    )
    return {
        "soap_version": service.soap_service.soap_version,
        "endpoints": endpoints,
        "wss_security": wss_security,
        "stuurgegevens": stuurgegevens,
    }
