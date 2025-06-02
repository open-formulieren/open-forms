from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute

PLUGIN_ID = "yivi_oidc"


class YiviAuthenticationAttributes(models.TextChoices):
    bsn = AuthAttribute.bsn.value, _("BSN")
    kvk = AuthAttribute.kvk.value, _("KvK number")
