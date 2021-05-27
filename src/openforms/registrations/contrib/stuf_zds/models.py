from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.SoapService",
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

    def get_client(self):
        from .client import StufZDSClient

        return StufZDSClient(self.service)
