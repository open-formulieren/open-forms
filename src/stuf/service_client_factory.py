from dataclasses import dataclass
from typing import Any

from soap.constants import EndpointSecurity, EndpointType

from .client import LoggingHook, noop_log
from .models import StufService
from .stuf import InvolvedParty, StufService, StuurGegevens, WSSecurity


@dataclass
class ServiceClientFactory:
    service: StufService
    request_log_hook: LoggingHook = noop_log
    response_log_hook: LoggingHook = noop_log

    def get_client_base_url(self) -> str:
        # while we have different endpoint types, the attached soap service itself also
        # defines a (potentially empty!) base URL which is normally used as fallback.
        return self.service.soap_service.url

    def get_client_session_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "verify": self.service.get_verify(),
            "cert": self.service.get_cert(),
            "auth": self.service.get_auth(),
        }
        return kwargs

    def get_client_init_kwargs(self):
        # pass the endpoint types map
        endpoints = {
            endpoint_type: self.service.get_endpoint(endpoint_type)
            for endpoint_type in EndpointType
        }
        wss_security = WSSecurity(
            use_wss=self.service.soap_service.endpoint_security
            in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth],
            wss_username=self.service.soap_service.user,
            wss_password=self.service.soap_service.password,
        )
        stuurgegevens = StuurGegevens(
            zender=InvolvedParty.from_service_configuration(self.service, "zender"),
            ontvanger=InvolvedParty.from_service_configuration(
                self.service, "ontvanger"
            ),
        )
        return {
            "soap_version": self.service.soap_service.soap_version,
            "endpoints": endpoints,
            "request_log_hook": self.request_log_hook,
            "response_log_hook": self.response_log_hook,
            "wss_security": wss_security,
            "stuurgegevens": stuurgegevens,
        }
