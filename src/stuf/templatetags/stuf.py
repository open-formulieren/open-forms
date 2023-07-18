from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

from django.template import Library
from django.utils import dateformat, timezone

from soap.constants import EndpointSecurity

from ..models import StufService

register = Library()


@register.inclusion_tag("stuf/includes/security.xml")
def render_security(service: StufService, expiry_minutes: int) -> dict[str, Any]:
    """
    Provide the security headers block based on service configuration.

    Note the formatting of the timestamps, according to the spec at
    https://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0.pdf
    (lines 1290 and further):

        This specification defines and illustrates time references in terms of the xsd:dateTime type
        defined in XML Schema. It is RECOMMENDED that all time references use this type. It is further
        RECOMMENDED that all references be in UTC time. Implementations MUST NOT generate time
        instants that specify leap seconds. If, however, other time types are used, then the ValueType
        attribute (described below) MUST be specified to indicate the data type of the time format.
        Requestors and receivers SHOULD NOT rely on other applications supporting time resolution
        finer than milliseconds.

    Hence we use a maximum resolution of seconds and ensure the source datetime is in
    UTC. The datetime module does not support leap seconds, so we should be safe in that
    regard.
    """
    # get 'now' in UTC
    now = timezone.localtime(timezone.now(), timezone=timezone.utc)
    expires_at = now + timedelta(minutes=expiry_minutes)
    return {
        "use_wss": (
            service.soap_service.endpoint_security
            in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth]
        ),
        "wss_username": service.soap_service.user,
        "wss_password": service.soap_service.password,
        "wss_created": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "wss_expires": expires_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


@dataclass
class InvolvedParty:
    applicatie: str
    organisatie: str = ""
    administratie: str = ""
    gebruiker: str = ""

    NAMES = (
        "applicatie",
        "organisatie",
        "administratie",
        "gebruiker",
    )

    @classmethod
    def from_service_configuration(
        cls,
        service: StufService,
        prefix: Literal["zender", "ontvanger"],
    ) -> "InvolvedParty":
        kwargs = {name: getattr(service, f"{prefix}_{name}", "") for name in cls.NAMES}
        return cls(**kwargs)


@register.inclusion_tag("stuf/includes/stuurgegevens.xml")
def render_stuurgegevens(service: StufService, referentienummer: str) -> dict[str, Any]:
    tijdstip_bericht = timezone.now()
    tijdstip_bericht = dateformat.format(tijdstip_bericht, "YmdHis")
    return {
        "zender": InvolvedParty.from_service_configuration(service, "zender"),
        "ontvanger": InvolvedParty.from_service_configuration(service, "ontvanger"),
        "referentienummer": referentienummer,
        "tijdstip_bericht": tijdstip_bericht,
    }
