from ape_pie.client import APIClient as SessionBase, is_base_url
from zeep.client import Client
from zeep.transports import Transport

from .models import SoapService
from .session_factory import SessionFactory


def build_client(
    service: SoapService,
    transport_factory=Transport,
    client_factory=Client,
    **kwargs,
) -> Client:
    """
    Build a :class:`zeep.Client` instance from a :class:`soap.models.SoapService` conf.

    The mTLS and authentication parameters are taken from the service configuration
    and configured on the session, which is then used as transport for the zeep client.

    Any additional kwargs are passed through to the :class:`zeep.Client` instantiation.
    """
    session_factory = SessionFactory(service)
    session = SOAPSession.configure_from(session_factory)
    transport = transport_factory(
        session=session,
        timeout=service.timeout,
        # operation_timeout gets passed as a parameter on all requests, overriding any
        # monkeypatched requests.Session defaults
        operation_timeout=service.timeout,
    )
    kwargs.setdefault("wsdl", service.url)
    client = client_factory(
        transport=transport,
        wsse=service.get_wsse(),
        **kwargs,
    )
    return client


class SOAPSession(SessionBase):
    def to_absolute_url(self, maybe_relative_url: str) -> str:
        """
        Disable base URL validation.

        SOAP services are typically configured with a WSDL which describes the bindings,
        and the base URL specified is maybe not relevant at all.
        """
        is_absolute = is_base_url(maybe_relative_url)
        if is_absolute:
            # remove the guard rails as they get in the way when configuring a service
            # with a WSDL URL.
            return maybe_relative_url

        # for relative paths -> use the default behaviour, which joins URLs against the
        # base URL.
        return super().to_absolute_url(maybe_relative_url)
