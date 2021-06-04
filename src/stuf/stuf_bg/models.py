from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from stuf.managers import ConfigManager


class StufBGConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.SoapService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    objects = ConfigManager()

    def get_client(self):
        from .client import StufBGClient

        if not self.service:
            raise RuntimeError("You must configure a service!")

        return StufBGClient(self.service)

    class Meta:
        verbose_name = _("StUF-BG configuration")
