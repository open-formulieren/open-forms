from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class HaalCentraalConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class HaalCentraalConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Haal Centraal API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")
