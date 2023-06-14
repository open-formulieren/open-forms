import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .client import HaalCentraalClient, HaalCentraalV1Client, HaalCentraalV2Client
from .constants import Attributes, AttributesV2, HaalCentraalVersion

logger = logging.getLogger(__name__)

VERSION_TO_ATTRIBUTES_MAP = {
    HaalCentraalVersion.haalcentraal13: Attributes,
    HaalCentraalVersion.haalcentraal20: AttributesV2,
}


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

    def build_client(self) -> HaalCentraalClient | None:
        if not self.service:
            logger.info(
                "Haal Centraal Config hasn't been setup properly, make sure to configure the service properly."
            )
            return

        match self.version:
            case HaalCentraalVersion.haalcentraal13:
                return HaalCentraalV1Client(self.service.build_client())
            case HaalCentraalVersion.haalcentraal20:
                return HaalCentraalV2Client(self.service.build_client())
            case _:
                logger.info(
                    "Haal Centraal Config hasn't been setup properly, make sure to configure the version properly."
                )
                return

    def get_attributes(self) -> Attributes | AttributesV2:
        if not self.service:
            return Attributes

        return VERSION_TO_ATTRIBUTES_MAP[self.version]
