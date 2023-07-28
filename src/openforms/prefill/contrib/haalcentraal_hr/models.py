import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

logger = logging.getLogger(__name__)


class HaalCentraalHRConfig(SingletonModel):
    """Configuration for the Haal Centraal HR Prefill"""

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Haal Centraal HR API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    class Meta:
        verbose_name = _("Haal Centraal HR configuration")

    def build_client(self):
        if not self.service:
            logger.info("No service configured for Haal Centraal HR.")
            return

        return self.service.build_client()
