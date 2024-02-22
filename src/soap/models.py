from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_certmanager.models import Certificate
from zeep.wsse.signature import Signature
from zeep.wsse.username import UsernameToken

from .constants import EndpointSecurity, SOAPVersion


class _Signature(Signature):
    def verify(self, envelope):
        return envelope


class SoapService(models.Model):
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_("Human readable label to identify services"),
    )
    url = models.URLField(
        _("URL"),
        blank=True,
        help_text=_("URL of the service to connect to."),
    )

    soap_version = models.CharField(
        _("SOAP version"),
        max_length=5,
        default=SOAPVersion.soap12,
        choices=SOAPVersion.choices,
        help_text=_("The SOAP version to use for the message envelope."),
    )
    timeout = models.PositiveSmallIntegerField(
        _("timeout"),
        help_text=_("Timeout (in seconds) for HTTP calls."),
        default=10,
    )

    endpoint_security = models.CharField(
        _("Security"),
        max_length=20,
        blank=True,
        choices=EndpointSecurity.choices,
        help_text=_("The security to use for messages sent to the endpoints."),
    )

    user = models.CharField(
        _("user"),
        max_length=200,
        blank=True,
        help_text=_("Username to use in the XML security context."),
    )
    password = models.CharField(
        _("password"),
        max_length=200,
        blank=True,
        help_text=_("Password to use in the XML security context."),
    )

    client_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_(
            "The SSL certificate file used for client identification. If left empty, mutual TLS is disabled."
        ),
        on_delete=models.PROTECT,
        related_name="soap_services_client",
    )
    server_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_("The SSL/TLS certificate of the server"),
        on_delete=models.PROTECT,
        related_name="soap_services_server",
    )

    class Meta:
        verbose_name = _("SOAP service")
        verbose_name_plural = _("SOAP services")

    def __str__(self):
        return self.label

    def get_cert(self) -> None | str | tuple[str, str]:
        certificate = self.client_certificate
        if not certificate:
            return None

        if certificate.public_certificate and certificate.private_key:
            return (certificate.public_certificate.path, certificate.private_key.path)

        if certificate.public_certificate:
            return certificate.public_certificate.path

        return None

    def get_verify(self) -> bool | str:
        certificate = self.server_certificate
        if certificate:
            return certificate.public_certificate.path
        return True

    def get_auth(self) -> tuple[str, str] | None:
        if (
            self.endpoint_security
            in [EndpointSecurity.basicauth, EndpointSecurity.wss_basicauth]
            and self.user
            and self.password
        ):
            return (self.user, self.password)
        return None

    def get_wsse(
        self,
    ) -> Signature | UsernameToken | tuple[UsernameToken, Signature] | None:
        sig = lambda: _Signature(
            self.client_certificate.private_key.path,
            self.client_certificate.public_certificate.path,
        )

        basic = lambda: UsernameToken(self.user, self.password)

        match self.endpoint_security:
            case EndpointSecurity.wss:
                return sig()
            case EndpointSecurity.wss_basicauth:
                return (basic(), sig())
            case EndpointSecurity.basicauth:
                return basic()
            case "":
                return None

        raise ValueError(
            f"invalid SoapService.endpoint_security: {self.endpoint_security}"
        )
