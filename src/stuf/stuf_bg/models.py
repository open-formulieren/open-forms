from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from stuf.managers import ConfigManager


class StufBGConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.StufService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    objects = ConfigManager()

    class Meta:
        verbose_name = _("StUF-BG configuration")
