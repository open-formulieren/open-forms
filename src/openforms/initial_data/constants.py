from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute


class SupportedAuthAttributes(models.TextChoices):
    bsn = "bsn", _("BSN")
    kvk = "kvk", _("KvK number")


# sanity check that we use a subset of existing attributes
assert all(choice in AuthAttribute for choice in SupportedAuthAttributes)
