from django.db import models
from django.utils.translation import gettext_lazy as _

from privates.fields import PrivateMediaFileField
from solo.models import SingletonModel


class SoapService(models.Model):
    ontvanger_organisatie = models.CharField(
        _("organisatie"), max_length=200, blank=True
    )
    ontvanger_applicatie = models.CharField(_("applicatie"), max_length=200, blank=True)
    # ontvanger_administratie = models.CharField(
    #     _("administratie"), max_length=200, blank=True
    # )
    # ontvanger_gebruiker = models.CharField(_("gebruiker"), max_length=200, blank=True)

    zender_organisatie = models.CharField(_("organisatie"), max_length=200, blank=True)
    zender_applicatie = models.CharField(_("applicatie"), max_length=200, blank=True)
    # zender_administratie = models.CharField(
    #     _("administratie"), max_length=200, blank=True
    # )
    # zender_gebruiker = models.CharField(_("gebruiker"), max_length=200, blank=True)

    url = models.URLField(
        _("url"),
        blank=True,
        help_text="URL of the StUF-ZDS service to connect to.",
    )
    user = models.CharField(
        _("user"),
        max_length=200,
        blank=True,
        help_text="Username to use in the XML security context.",
    )
    password = models.CharField(
        _("password"),
        max_length=200,
        blank=True,
        help_text="Password to use in the XML security context.",
    )

    certificate = PrivateMediaFileField(
        upload_to="certificate/",
        blank=True,
        null=True,
        help_text="The SSL certificate file used for client identification. If left empty, mutual TLS is disabled.",
    )
    certificate_key = PrivateMediaFileField(
        upload_to="certificate/",
        help_text="The SSL certificate key file used for client identification. If left empty, mutual TLS is disabled.",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Soap Service")

    def build_client(self):
        from .client import StufZDSClient

        return StufZDSClient(self)


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    soap_service = models.ForeignKey(
        "SoapService",
        on_delete=models.PROTECT,
        related_name="stuf_zds_config",
        null=True,
    )

    gemeentecode = models.CharField(max_length=32)

    def apply_defaults_to(self, options):
        options.setdefault("gemeentecode", self.gemeentecode)
