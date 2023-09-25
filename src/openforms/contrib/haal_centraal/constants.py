from django.db import models


class BRPVersions(models.TextChoices):
    """
    Supported (and tested) versions of the Haal Centraal BRP Personen API.
    """

    v13 = "1.3", "BRP Personen Bevragen 1.3"
    v20 = "2.0", "BRP Personen Bevragen 2.0"
