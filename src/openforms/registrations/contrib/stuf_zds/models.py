from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class StufZDSConfigManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.select_related("service")


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

    gemeentecode = models.CharField(
        _("Municipality code"),
        max_length=32,
        help_text=_("Municipality code to register zaken"),
    )
    zds_zaaktype_code = models.CharField(
        _("Zaaktype code"),
        max_length=32,
        help_text=_("Zaaktype code for newly created zaken in StUF-ZDS"),
    )
    zds_zaaktype_omschrijving = models.CharField(
        _("Zaaktype description"),
        max_length=32,
        help_text=_("Zaaktype description for newly created zaken in StUF-ZDS"),
    )

    objects = StufZDSConfigManager()

    def apply_defaults_to(self, options):
        options.setdefault("gemeentecode", self.gemeentecode)
        options.setdefault("zds_zaaktype_code", self.zds_zaaktype_code)
        options.setdefault("zds_zaaktype_omschrijving", self.zds_zaaktype_omschrijving)

    def get_client(self, options):
        from .client import StufZDSClient

        return StufZDSClient(self.service, options)

    class Meta:
        verbose_name = _("StUF-ZDS configuration")
