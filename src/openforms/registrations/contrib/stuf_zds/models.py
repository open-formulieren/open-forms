from django.db import models
from django.utils.translation import gettext_lazy as _

from privates.fields import PrivateMediaFileField
from solo.models import SingletonModel


class SoapService(models.Model):
    ontvanger_organisatie = models.CharField(_("ontvanger organisatie"), max_length=200)
    ontvanger_applicatie = models.CharField(_("ontvanger applicatie"), max_length=200)
    # ontvanger_administratie = models.CharField(
    #     _("ontvanger administratie"), max_length=200
    # )
    # ontvanger_gebruiker = models.CharField(_("ontvanger gebruiker"), max_length=200)

    zender_organisatie = models.CharField(_("zender organisatie"), max_length=200)
    zender_applicatie = models.CharField(_("zender applicatie"), max_length=200)
    # zender_administratie = models.CharField(
    #     _("zender administratie"), max_length=200
    # )
    # zender_gebruiker = models.CharField(_("zender gebruiker"), max_length=200)

    url = models.URLField(
        _("url"),
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
        upload_to="certificate/",
        blank=True,
        null=True,
        help_text=_(
            "The SSL certificate file used for client identification. If left empty, mutual TLS is disabled."
        ),
    )
    certificate_key = PrivateMediaFileField(
        upload_to="certificate/",
        help_text=_(
            "The SSL certificate key file used for client identification. If left empty, mutual TLS is disabled."
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Soap Service")

    def build_client(self):
        from .client import StufZDSClient

        return StufZDSClient(self)

    def __str__(self):
        # ???
        return f"{self.url}"


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "SoapService",
        on_delete=models.PROTECT,
        related_name="stuf_zds_config",
        null=True,
    )

    gemeentecode = models.CharField(_("Gemeentecode to register Zaken"), max_length=32)
    zds_zaaktype_code = models.CharField(
        _("Zaaktype code for newly created Zaken in StUF-ZDS"), max_length=32
    )
    zds_zaaktype_omschrijving = models.CharField(
        _("Zaaktype description for newly created Zaken in StUF-ZDS"),
        max_length=32,
    )

    def apply_defaults_to(self, options):
        options.setdefault("gemeentecode", self.gemeentecode)
        options.setdefault("zds_zaaktype_code", self.zds_zaaktype_code)
        options.setdefault("zds_zaaktype_omschrijving", self.zds_zaaktype_omschrijving)
