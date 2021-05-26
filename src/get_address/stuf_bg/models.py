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
