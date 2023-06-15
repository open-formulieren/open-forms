import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .client import HaalCentraalClient, HaalCentraalV1Client, HaalCentraalV2Client
from .constants import Attributes, AttributesV2, HaalCentraalVersion

logger = logging.getLogger(__name__)

VERSION_TO_ATTRIBUTES_MAP: Attributes | AttributesV2 = {
    HaalCentraalVersion.haalcentraal13: Attributes,
    HaalCentraalVersion.haalcentraal20: AttributesV2,
}

VERSION_TO_CLIENT_CLASS_MAP: HaalCentraalClient = {
    HaalCentraalVersion.haalcentraal13: HaalCentraalV1Client,
    HaalCentraalVersion.haalcentraal20: HaalCentraalV2Client,
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
        ClientCls = VERSION_TO_CLIENT_CLASS_MAP.get(self.version)
        if not self.service or ClientCls is None:
            logger.info(
                "Haal Centraal Config hasn't been setup properly, make sure to configure the service properly."
            )
            return None
        return ClientCls(self.service.build_client())

    def get_attributes(self) -> Attributes | AttributesV2:
        if not self.service:
            return Attributes

        return VERSION_TO_ATTRIBUTES_MAP[self.version]
