from django.db import models
from django.utils.translation import gettext_lazy as _

from zgw_consumers.models import Certificate

from stuf.constants import EndpointSecurity, SOAPVersion


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


class StufService(models.Model):

    soap_service = models.OneToOneField(
        SoapService,
        on_delete=models.CASCADE,
        related_name="stuf_service",
        help_text=_("The soap service this stuf service uses"),
    )

    ontvanger_organisatie = models.CharField(
        _("receiving organisation"),
        help_text=_("Field 'ontvanger organisatie' in StUF"),
        max_length=200,
        blank=True,
    )
    ontvanger_applicatie = models.CharField(
        _("receiving application"),
        help_text=_("Field 'ontvanger applicatie' in StUF"),
        max_length=200,
    )
    ontvanger_administratie = models.CharField(
        _("receiving administration"),
        help_text=_("Field 'ontvanger administratie' in StUF"),
        max_length=200,
        blank=True,
    )
    ontvanger_gebruiker = models.CharField(
        _("receiving user"),
        help_text=_("Field 'ontvanger gebruiker' in StUF"),
        max_length=200,
        blank=True,
    )

    zender_organisatie = models.CharField(
        _("sending organisation"),
        help_text=_("Field 'zender organisatie' in StUF"),
        max_length=200,
        blank=True,
    )
    zender_applicatie = models.CharField(
        _("sending application"),
        help_text=_("Field 'zender applicatie' in StUF"),
        max_length=200,
    )
    zender_administratie = models.CharField(
        _("sending administration"),
        help_text=_("Field 'zender administratie' in StUF"),
        max_length=200,
        blank=True,
    )
    zender_gebruiker = models.CharField(
        _("sending user"),
        help_text=_("Field 'zender gebruiker' in StUF"),
        max_length=200,
        blank=True,
    )

    endpoint_beantwoord_vraag = models.URLField(
        _("endpoint BeantwoordVraag"),
        blank=True,
        help_text=_(
            "Endpoint for synchronous request messages, usually '[...]/BeantwoordVraag'"
        ),
    )
    endpoint_vrije_berichten = models.URLField(
        _("endpoint VrijeBerichten"),
        blank=True,
        help_text=_(
            "Endpoint for synchronous free messages, usually '[...]/VerwerkSynchroonVrijBericht' or '[...]/VrijeBerichten'."
        ),
    )
    endpoint_ontvang_asynchroon = models.URLField(
        _("endpoint OntvangAsynchroon"),
        blank=True,
        help_text=_(
            "Endpoint for asynchronous messages, usually '[...]/OntvangAsynchroon'."
        ),
    )

    class Meta:
        verbose_name = _("StUF service")
        verbose_name_plural = _("StUF services")

    def get_cert(self):
        cert = (
            (self.certificate.path, self.certificate_key.path)
            if self.certificate and self.certificate_key
            else (None, None)
        )

        return cert

    def get_endpoint(self, type):
        attr = f"endpoint_{type}"

        if not hasattr(self, attr):
            raise ValueError(f"Endpoint type {type} does not exist.")

        val = getattr(self, attr, None)
        return val or self.soap_service.url

    def get_auth(self):
        if (
            self.endpoint_security
            in [EndpointSecurity.basicauth, EndpointSecurity.wss_basicauth]
            and self.user
            and self.password
        ):
            return (self.user, self.password)
        return (None, None)

    def __str__(self):
        return self.soap_service.label
