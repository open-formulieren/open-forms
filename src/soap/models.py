from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_certmanager.models import Certificate
from zeep.client import Client

from .constants import EndpointSecurity, SOAPVersion


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

    def build_client(self) -> Client:
        """
        Build an SOAP API client from the service configuration.
        """
        client = Client(self.url)
        # auth can be added to zeep.Client in the future if needed
        return client
