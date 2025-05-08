from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute

PLUGIN_ID = "yivi_oidc"


class YiviAuthenticationAttributes(models.TextChoices):
    bsn = AuthAttribute.bsn, _("BSN")
    kvk = AuthAttribute.kvk, _("KvK number")
    pseudo = AuthAttribute.pseudo, _("Pseudo ID")
