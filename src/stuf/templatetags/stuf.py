from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from django.template import Library
from django.utils import dateformat, timezone

from ..constants import EndpointSecurity
from ..models import StufService

register = Library()


DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
DATETIME_FORMAT = "%Y%m%d%H%M%S"


def fmt_soap_datetime(d: datetime) -> str:
    return d.strftime(DATETIME_FORMAT)


def fmt_soap_date(d: datetime) -> str:
    return d.strftime(DATE_FORMAT)


def fmt_soap_time(d: datetime) -> str:
    return d.strftime(TIME_FORMAT)


@register.inclusion_tag("stuf/includes/security.xml")
def render_security(service: StufService, expiry_minutes: int) -> dict[str, Any]:
    """
    Provide the security headers block based on service configuration.
    """
    now = timezone.now()
    expires_at = now + timedelta(minutes=expiry_minutes)
    return {
        "use_wss": (
            service.soap_service.endpoint_security
            in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth]
        ),
        "wss_username": service.soap_service.user,
        "wss_password": service.soap_service.password,
        # uh - fmt as date seems wrong? what's the point of specifying an expiry in
        # minutes if you truncate the time part??? This is taken from the StUF-ZDS
        # implementation, note that StUF-BG does not format at all!
        "wss_created": fmt_soap_date(now),
        "wss_expires": fmt_soap_date(expires_at),
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
def render_stuurgegevens(
    service: StufService,
    referentienummer: str,
    tijdstip_bericht: datetime | str | None = None,
) -> dict[str, Any]:
    if tijdstip_bericht is None:
        tijdstip_bericht = timezone.now()
    if isinstance(tijdstip_bericht, datetime):
        tijdstip_bericht = dateformat.format(tijdstip_bericht, "YmdHis")
    return {
        "zender": InvolvedParty.from_service_configuration(service, "zender"),
        "ontvanger": InvolvedParty.from_service_configuration(service, "ontvanger"),
        "referentienummer": referentienummer,
        "tijdstip_bericht": tijdstip_bericht,
    }
