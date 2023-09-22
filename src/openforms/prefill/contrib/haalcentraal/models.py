import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.contrib.haal_centraal.constants import BRPVersions

from .client import HaalCentraalClient, HaalCentraalV1Client, HaalCentraalV2Client
from .constants import Attributes, AttributesV2, HaalCentraalVersion

logger = logging.getLogger(__name__)


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
    version = models.CharField(
        _("API version"),
        max_length=30,
        choices=HaalCentraalVersion.choices,
        default=HaalCentraalVersion.haalcentraal13,
        help_text=_("The API version provided by the selected service."),
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")

    def get_attributes(self) -> type[Attributes] | type[AttributesV2]:
        if not self.service:
            return Attributes

        return VERSION_TO_ATTRIBUTES_MAP[self.version]
