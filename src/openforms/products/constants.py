from django.db import models
from django.utils.translation import gettext as _

CONTENT_LABELS_LOOKUP_CACHE_TIMEOUT = 60 * 60  # 1 hour


class ProductSourceChoices(models.TextChoices):
    local = "local", _("Local")
    open_product = "open_product", _("Open product")
