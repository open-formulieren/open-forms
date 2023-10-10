import logging
from dataclasses import dataclass, field
from typing import Any, TypeVar

from requests.auth import AuthBase
from requests.models import PreparedRequest
from zds_client import ClientAuth
from zgw_consumers.constants import AuthTypes
from zgw_consumers.models import Service

from .nlx import NLXClient

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=NLXClient)


def build_client(service: Service, client_factory: type[T] = NLXClient, **kwargs) -> T:
    """
    Build a client for a given :class:`zgw_consumers.models.Service`.

    :arg service: The model instance holding the service configuration.
    :arg client_factory: Particular client (sub)class for more specialized clients.

    Any additional keyword arguments are forwarded to the client initialization.
    """
    factory = ServiceClientFactory(service)
    return client_factory.configure_from(factory, nlx_base_url=service.nlx, **kwargs)


@dataclass
class ServiceClientFactory:
    """
    Map zgw_consumers.Service model configuration to API client parameters.
    """

    service: Service

    def get_client_base_url(self) -> str:
        """
        Use the configured API root as client base URL.
        """
        return self.service.api_root

    def get_client_session_kwargs(self) -> dict[str, Any]:
        """
        Pass connection parameters from the configured service.

        * mTLS configuration from uploaded/configured certificates
        * authentication type and credentials from DB configuration
        """
        kwargs = {}

        # mTLS: verify server certificate if configured
        if server_cert := self.service.server_certificate:
            # NOTE: this only works with a file-system based storage!
            kwargs["verify"] = server_cert.public_certificate.path

        # mTLS: offer client certificate if configured
        if client_cert := self.service.client_certificate:
            client_cert_path = client_cert.public_certificate.path
            # decide between single cert or cert,key tuple variant
            kwargs["cert"] = (
                (client_cert_path, privkey.path)
                if (privkey := client_cert.private_key)
                else client_cert_path
            )

        match self.service.auth_type:
            case AuthTypes.api_key:
                kwargs["auth"] = APIKeyAuth(
                    header=self.service.header_key, key=self.service.header_value
                )
            case AuthTypes.zgw:
                kwargs["auth"] = ZGWAuth(service=self.service)

        return kwargs


@dataclass
class APIKeyAuth(AuthBase):
    """
    Requests authentication class for API key-based auth (in the request headers).
    """

    header: str
    key: str

    def __call__(self, request: PreparedRequest):
        request.headers[self.header] = self.key
        return request


@dataclass
class ZGWAuth(AuthBase):
    """
    Requests authentication class for JWT-based ZGW auth.
    """

    service: Service
    auth: ClientAuth = field(init=False)

    def __post_init__(self):
        self.auth = ClientAuth(
            client_id=self.service.client_id,
            secret=self.service.secret,
            user_id=self.service.user_id,
            user_representation=self.service.user_representation,
        )

    def __call__(self, request: PreparedRequest):
        request.headers.update(self.auth.credentials())
        return request
