from django.conf import settings

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

    .. todo:: Incorporate `WS-Security <https://docs.python-zeep.org/en/master/wsse.html>`_
       concepts (see Chris' PR for Suwinet).
    """
    session_factory = SessionFactory(service)
    session = SOAPSession.configure_from(session_factory)
    transport = transport_factory(
        session=session,
        timeout=settings.DEFAULT_TIMEOUT_REQUESTS,
    )
    client = client_factory(
        service.url,
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
