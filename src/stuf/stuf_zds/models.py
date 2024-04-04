from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class StufZDSConfigManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.select_related("service", "service__soap_service")


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.StufService",
        on_delete=models.PROTECT,
        related_name="stuf_zds_config",
        null=True,
    )

    objects = StufZDSConfigManager()

    class Meta:
        verbose_name = _("StUF-ZDS configuration")
