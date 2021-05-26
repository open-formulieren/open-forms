from django.db import models
from solo.models import SingletonModel


class StufBGConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf_zds.SoapService",
        on_delete=models.PROTECT,
        related_name="stuf_bg_config",
        null=True,
    )

    def get_client(self):
        from .client import StufBGClient

        if not self.service:
            raise RuntimeError("You must configure a service!")

        return StufBGClient(self.service)
