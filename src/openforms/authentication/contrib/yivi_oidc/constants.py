from django.db import models
from django.utils.translation import gettext_lazy as _

PLUGIN_ID = "yivi_oidc"


class YiviAuthenticationAttributes(models.TextChoices):
    bsn = "bsn", _("BSN")
    kvk = "kvk", _("KvK number")
    pseudo = "pseudo", _("Pseudo ID")
