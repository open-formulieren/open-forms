from datetime import UTC, timedelta
from typing import Any

from django.template import Library
from django.utils import dateformat, timezone

from ..client import StuurGegevens, WSSecurity

register = Library()


@register.inclusion_tag("stuf/includes/security.xml")
def render_security(wss: WSSecurity, expiry_minutes: int) -> dict[str, Any]:
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
    now = timezone.localtime(timezone.now(), timezone=UTC)
    expires_at = now + timedelta(minutes=expiry_minutes)
    return {
        "use_wss": wss.use_wss,
        "wss_username": wss.wss_username,
        "wss_password": wss.wss_password,
        "wss_created": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "wss_expires": expires_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


@register.inclusion_tag("stuf/includes/stuurgegevens.xml")
def render_stuurgegevens(
    stuurgegevens: StuurGegevens, referentienummer: str
) -> dict[str, Any]:
    tijdstip_bericht = timezone.now()
    tijdstip_bericht = dateformat.format(tijdstip_bericht, "YmdHis")
    return {
        "zender": stuurgegevens.zender,
        "ontvanger": stuurgegevens.ontvanger,
        "referentienummer": referentienummer,
        "tijdstip_bericht": tijdstip_bericht,
    }
