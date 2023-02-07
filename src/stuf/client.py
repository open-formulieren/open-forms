"""
Provide a StUF client base class.

`StUF <https://www.gemmaonline.nl/index.php/StUF_Berichtenstandaard>`_ is an information
exchange message format defined by VNG/GEMMA. It extends SOAP/XML, in particular by
providing a base XML schema and XSDs to validate these schema's. Domain "koppelvlakken"
use StUF as base by further extending it with domain-specific schema's for the actual
content/information being exchanged.

The base class here provides the shared mechanisms for StUF v3 that are domain-agnostic.
Whenever you are implementing a particular StUF integration, you are expected to
subclass the base class and implement your domain specific logic in your own class.
"""
import logging
import uuid
from contextlib import contextmanager
from typing import Any, Literal, Protocol, cast

from django.template import loader

from requests import Session
from requests.models import Response

from .constants import SOAP_VERSION_CONTENT_TYPES, EndpointType
from .models import StufService

logger = logging.getLogger(__name__)


class LoggingHook(Protocol):
    def __call__(self, service: StufService, url: str) -> None:
        ...  # pragma: nocover


@contextmanager
def _maybe_close_session(client: "BaseClient"):
    _should_close = not client._in_context_manager
    try:
        yield client.session
    finally:
        if _should_close and client._session is not None:
            client._session.close()


def noop(*args, **kwargs) -> None:
    pass


class BaseClient:
    """
    Wrap the requests :class:`requests.Session` and own service-configuration.

    The base client provides the mechanisms to support connection pooling. Opt-in to
    this behaviour by using the client as a context manager:

    >>> with MyClient() as client:
    >>>     client.do_the_thing()

    This client also provides the generic template context for the StUF/SOAP envelopes.
    Ideally, you would render an XML template which extends the base template, focusing
    on your sector/domain specific markup. For example:

    .. code-block:: django

        {% extends "stuf/soap_envelope.xml" %}{% load stuf %}
        {% block body %}
            <SN:operation
                xmlns:SN="sector-namespace"
                {additionalnamespaces used}
            >
                <SN:stuurgegevens>
                    <StUF:berichtcode>Lk01</StUF:berichtcode>
                    {% render_stuurgegevens service referentienummer %}
                    <StUF:entiteittype>ZAK</StUF:entiteittype>
                </SN:stuurgegevens>
                ...
            </SN:operation>
        {% endblock %}

    """

    sector_alias: str = ""
    """
    The sector/domain code for you concrete subclass.

    Must be set by the subclass, example value are 'bg' or 'zkn'. This is used in
    building up the ``SOAPAction`` HTTP header.
    """
    soap_security_expires_minutes: int
    """
    Specify how long a SOAP request is valid after creation.

    Used in the Security element of the SOAP envelope. Must be set by subclass.
    """

    _session: Session | None = None
    _in_context_manager: bool = False

    def __init__(
        self,
        service: StufService,
        request_log_hook: LoggingHook = noop,
        response_log_hook: LoggingHook = noop,
    ):
        self.service = service
        self.request_log_hook = request_log_hook
        self.response_log_hook = response_log_hook

    def __enter__(self):
        self._in_context_manager = True
        return self

    def __exit__(self, *args):
        if self._session is not None:
            self.session.close()
        self._in_context_manager = False

    #
    # HTTP interaction
    #

    @property
    def session(self) -> Session:
        """
        Wrap the requests Session.
        """
        if self._session is None:
            self._session = Session()
        return self._session

    def _get_auth_kwargs(self):
        cert = self.service.get_cert()
        auth = self.service.get_auth()
        verify = self.service.get_verify()
        return {"cert": cert, "auth": auth, "verify": verify}

    def _build_headers(self, soap_action: str) -> dict[str, str]:
        soap_version = self.service.soap_service.soap_version
        headers = {
            "Content-Type": SOAP_VERSION_CONTENT_TYPES[soap_version],
            "SOAPAction": (
                "http://www.egem.nl/StUF/sector/"
                f"{self.sector_alias}/0310/{soap_action}"
            ),
        }
        return headers

    def _log(self, url: str, *, direction: Literal["request", "response"]) -> None:
        match direction:
            case "request":
                hook = self.request_log_hook
            case "response":
                hook = self.response_log_hook
            case _:  # pragma: nocover
                raise ValueError("Unexpected direction received")
        hook(self.service, url)

    def request(
        self,
        soap_action: str,
        body: str,
        endpoint_type: str = cast(str, EndpointType.vrije_berichten),
    ) -> Response:
        self_cls = type(self)

        url = self.service.get_endpoint(type=endpoint_type)
        logger.debug(
            "%r client (SOAP) request.\nurl: %s\ndata: %s",
            self_cls,
            url,
            body,
            extra={"url": url, "client": self_cls, "body": body},
        )
        auth_kwargs = self._get_auth_kwargs()
        headers = self._build_headers(soap_action)

        with _maybe_close_session(self) as session:
            self._log(url, direction="request")
            response = session.post(
                url,
                data=body.encode("utf-8"),
                headers=headers,
                **auth_kwargs,
            )
            logger.debug(
                "%r client response.\nurl: %s\nresponse content: %s",
                self_cls,
                url,
                response.content,
                extra={"url": url, "client": self_cls, "response": response.content},
            )
            self._log(url, direction="response")
            # TODO should this do response.raise_for_error() ?

        return response

    #
    # XML templating related methods
    #

    def build_base_context(self) -> dict[str, Any]:
        """
        Create the base context derived from the dynamic service configuration.
        """
        # the referentienummer may be overridden later on!
        referentienummer = uuid.uuid4()
        return {
            "soap_version": self.service.soap_service.soap_version,
            # context for security tag
            "service": self.service,
            "security_expires_minutes": self.soap_security_expires_minutes,
            # meta-information
            "referentienummer": referentienummer,
        }

    def templated_request(
        self,
        soap_action: str,
        template: str,
        context: dict[str, Any] | None = None,
        endpoint_type: str = cast(str, EndpointType.vrije_berichten),
    ) -> Response:
        """
        Make a request by templating out a template with the provided context.

        The context is merged with the base context and the resolved template is
        rendered into a string, suitable to be passed down to :meth:`request`.
        """
        full_context = {**self.build_base_context(), **(context or {})}
        ref_nr = full_context["referentienummer"]
        logger.debug(
            "Making StUF-%r request with referentienummer %s",
            self.sector_alias.upper(),
            ref_nr,
            extra={"ref_nr": ref_nr, "sector_alias": self.sector_alias},
        )
        body = loader.render_to_string(template, full_context)
        response = self.request(soap_action, body=body, endpoint_type=endpoint_type)
        return response
