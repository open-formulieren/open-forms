from django.db import models
from django.utils.translation import gettext_lazy as _


class EndpointSecurity(models.TextChoices):
    basicauth = "basicauth", _("Basic authentication")
    wss = "wss", _("SOAP extension: WS-Security")
    wss_basicauth = "wss_basicauth", _("Both")


class SOAPVersion(models.TextChoices):
    soap11 = "1.1", "SOAP 1.1"
    soap12 = "1.2", "SOAP 1.2"


SOAP_VERSION_CONTENT_TYPES = {
    SOAPVersion.soap11: "text/xml",
    SOAPVersion.soap12: "application/soap+xml",
}

assert [
    version in SOAP_VERSION_CONTENT_TYPES for version, _ in SOAPVersion.choices
], "Not all SOAP versions are present in the SOAP_VERSION_CONTENT_TYPES constant"
