from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KVKConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class KVKConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Zoeken"),
        help_text=_("API used for validation of KvK, RSIN and vestigingsnummer's"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    profiles = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Basisprofiel"),
        help_text=_("API used to retrieve basis profielen"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = KVKConfigManager()

    class Meta:
        verbose_name = _("KvK configuration")
