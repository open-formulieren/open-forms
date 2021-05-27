from django.db import models
from django.utils.translation import gettext_lazy as _

from privates.fields import PrivateMediaFileField


class SoapService(models.Model):
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_("Human readable label to identify services"),
    )
    ontvanger_organisatie = models.CharField(
        _("receiving organisation"),
        help_text=_("Field 'ontvanger organisatie' in StUF"),
        max_length=200,
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

    url = models.URLField(
        _("URL"),
        help_text=_("URL of the StUF-ZDS service to connect to."),
    )
    endpoint_sync = models.CharField(
        _("endpoint sync requests"),
        max_length=200,
        blank=True,
        help_text=_(
            "Endpoint for synchronous Soap request, for example '/VerwerkSynchroonVrijBericht'."
        ),
    )
    endpoint_async = models.CharField(
        _("endpoint async requests"),
        help_text=_(
            "Endpoint for asynchronous Soap request, usually '/OntvangAsynchroon'."
        ),
        max_length=200,
        blank=True,
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

    certificate = PrivateMediaFileField(
        upload_to="stuf/certificate/",
        blank=True,
        null=True,
        help_text=_(
            "The SSL certificate file used for client identification. If left empty, mutual TLS is disabled."
        ),
    )
    certificate_key = PrivateMediaFileField(
        upload_to="stuf/certificate/",
        help_text=_(
            "The SSL certificate key file used for client identification. If left empty, mutual TLS is disabled."
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("SOAP service")
        verbose_name_plural = _("SOAP services")

    def __str__(self):
        return f"{self.label} ({self.url})"
