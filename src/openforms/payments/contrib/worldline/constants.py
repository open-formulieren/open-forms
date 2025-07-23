from django.db import models
from django.utils.translation import gettext_lazy as _


class WordlineEndpoints(models.TextChoices):
    test = (
        "https://payment.preprod.direct.worldline-solutions.com",
        _("Worldline Test"),
    )
    live = "https://payment.direct.worldline-solutions.com", _("Worldline Live")
