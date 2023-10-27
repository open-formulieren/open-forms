from __future__ import annotations

from collections.abc import Mapping

from zeep.proxy import ServiceProxy
from zeep.transports import Transport

from soap.client import build_client

from .constants import SERVICES
from .models import SuwinetConfig


class NoServiceConfigured(RuntimeError):
    pass


def get_client(config: SuwinetConfig | None = None) -> SuwinetClient:
    config = config or SuwinetConfig.get_solo()

    if not config.service:
        raise NoServiceConfigured("You must configure a service!")

    return SuwinetClient(config)


class SuwinetClient(Mapping[str, ServiceProxy]):
    "A facade around Suwinet subservices that lazily loads and mounts service endpoints"

    def __init__(self, config: SuwinetConfig):
        self._config = config
        self._transport: Transport | None = None

    def _transport_factory(self, *args, **kwargs):
        "Share the transport over all subclients"
        self._transport = self._transport or Transport(*args, **kwargs)
        return self._transport

    def __exit__(self, *args, **kwargs):
        match self._transport:
            case Transport(session=session):
                session.close()
                self._transport = None

    def __enter__(self):
        return self

    def __getitem__(self, service_name: str) -> ServiceProxy:
        service = SERVICES[service_name]
        if not (address := self._config.get_binding_address(service)):
            raise KeyError(f"{service_name} not configured")

        client = build_client(
            service=self._config.service,
            wsdl=service.wsdl_path,
            transport_factory=self._transport_factory,
        )
        assert len(client.wsdl.bindings) == 1

        binding = list(client.wsdl.bindings.values())[0].name.text

        return client.create_service(binding, address)

    def __iter__(self):
        return (
            service.name
            for service in SERVICES.values()
            if self._config.get_binding_address(service)
        )

    def __dir__(self):
        yield from self
        yield from super().__dir__()

    def __len__(self):
        return sum(1 for service_name in self)

    def __getattr__(self, service_name: str) -> ServiceProxy:
        try:
            return self[service_name]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{service_name}'"
            ) from e
