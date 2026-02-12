"""
Provide a StUF client base class.

`StUF <https://vng-realisatie.github.io/StUF-onderlaag/>`_ is an information
exchange message format defined by VNG/GEMMA. It extends SOAP/XML, in particular by
providing a base XML schema and XSDs to validate these schema's. Domain "koppelvlakken"
use StUF as base by further extending it with domain-specific schema's for the actual
content/information being exchanged.

The base class here provides the shared mechanisms for StUF v3 that are domain-agnostic.
Whenever you are implementing a particular StUF integration, you are expected to
subclass the base class and implement your domain specific logic in your own class.
"""

import uuid
from typing import Any

from django.template import loader

import structlog
from ape_pie import APIClient, InvalidURLError
from ape_pie.client import is_base_url
from requests.models import Response

from soap.constants import SOAP_VERSION_CONTENT_TYPES, SOAPVersion

from .constants import EndpointType
from .stuf import StuurGegevens, WSSecurity

logger = structlog.stdlib.get_logger(__name__)


class BaseClient(APIClient):
    """
    A base client with :class:`requests.Session`'s interface.

    The base client provides the mechanisms to support connection pooling. Opt-in to
    this behaviour by using the client as a context manager:

    >>> with MyClient.configure_from(stuf_service) as client:
    >>>     client.do_the_thing()

    This client provides the generic template context for the StUF/SOAP envelopes.
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
                    {% render_stuurgegevens stuurgegevens referentienummer %}
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

    def __init__(
        self,
        base_url: str,
        request_kwargs: dict[str, Any] | None = None,
        *,
        soap_version: SOAPVersion = SOAPVersion.soap12,
        endpoints: dict[EndpointType | str, str],
        wss_security: WSSecurity,
        stuurgegevens: StuurGegevens,
    ):
        super().__init__(base_url, request_kwargs)

        self.soap_version = soap_version
        self._endpoints = endpoints
        self.wss_security = wss_security
        self.stuurgegevens = stuurgegevens

        # set the correct Content-Type header for the specified soap version
        self.headers["Content-Type"] = SOAP_VERSION_CONTENT_TYPES[self.soap_version]

    def to_absolute_url(self, maybe_relative_url: str | EndpointType) -> str:
        # Override of the base client behaviour - StUF clients support multiple
        # "base URLs" depending on the endpoint type which could *technically* not
        # share a common prefix. SOAP doesn't really use URL-based routing that much,
        # the operations are baked into the request body, so in this case, the
        # maybe_relative_url should always be a member of EndpointType enum.
        #
        # So either we get a fully qualified URL, which should thus be prefixed by one
        # of the values of self._endpoints, or we get a relative URL which is and
        # endpoint type and we can look it up from the mapping table.
        known_bases = list(self._endpoints.values())

        if is_base_url(maybe_relative_url):
            if not any(maybe_relative_url.startswith(base) for base in known_bases):
                raise InvalidURLError(
                    f"Target URL {maybe_relative_url} has a different base URL than the "
                    f"client's possible bases ({known_bases})."
                )
            return maybe_relative_url

        if (url := self._endpoints.get(maybe_relative_url)) is None:
            raise InvalidURLError(
                f"Endpoint type / relative URL {maybe_relative_url} is unknown in the "
                f"client's endpoints: {self._endpoints}."
            )
        return url

    #
    # HTTP interaction
    #

    def soap_request(
        self,
        soap_action: str,
        body: str,
        endpoint_type: EndpointType = EndpointType.vrije_berichten,
    ) -> Response:
        normalized_url = self.to_absolute_url(endpoint_type)
        log = logger.bind(
            client=type(self).__name__,
            url=normalized_url,
            soap_action=soap_action,
        )

        log.debug("stuf_request_started")
        response = self.post(
            normalized_url,
            data=body.encode("utf-8"),
            # See https://docs.python-requests.org/en/latest/user/advanced/#session-objects,
            # both the session.headers and these run-time headers are sent.
            headers={
                "SOAPAction": (
                    "http://www.egem.nl/StUF/sector/"
                    f"{self.sector_alias}/0310/{soap_action}"
                ),
            },
        )
        log.debug("stuf_response_received", status_code=response.status_code)
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
            "soap_version": self.soap_version,
            # context for security tag
            "wss_security": self.wss_security,
            "stuurgegevens": self.stuurgegevens,
            "security_expires_minutes": self.soap_security_expires_minutes,
            # meta-information
            "referentienummer": referentienummer,
        }

    def templated_request(
        self,
        soap_action: str,
        template: str,
        context: dict[str, Any] | None = None,
        endpoint_type: EndpointType = EndpointType.vrije_berichten,
    ) -> Response:
        """
        Make a request by templating out a template with the provided context.

        The context is merged with the base context and the resolved template is
        rendered into a string, suitable to be passed down to :meth:`request`.
        """
        full_context = {**self.build_base_context(), **(context or {})}
        structlog.contextvars.bind_contextvars(
            standard="StUF",
            sector_alias=self.sector_alias.upper(),
            soap_action=soap_action,
            referentienummer=full_context["referentienummer"],
        )
        logger.debug("prepare_and_make_request")
        body = loader.render_to_string(template, full_context)
        response = self.soap_request(
            soap_action, body=body, endpoint_type=endpoint_type
        )
        return response
