from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from stuf.managers import ConfigManager


class JccConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.SoapService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    objects = ConfigManager()

    def get_client(self):
        from .plugin import Plugin

        if not self.service:
            raise RuntimeError("You must configure a service!")

        return Plugin(self.service.url)

    class Meta:
        verbose_name = _("JCC configuration")
