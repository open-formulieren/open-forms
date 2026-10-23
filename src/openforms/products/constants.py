from collections.abc import Mapping

from django.db import models
from django.utils.translation import gettext as _

CONTENT_LABELS_LOOKUP_CACHE_TIMEOUT = 60 * 60


class OpenProductApiOptions(models.TextChoices):
    product = "product", _("Product API type")
    product_type = "producttypen", _("Producttype API type")


OPEN_PRODUCT_API_MAPPINGS: Mapping[OpenProductApiOptions, str] = {
    OpenProductApiOptions.product: "/producten/api/v1",
    OpenProductApiOptions.product_type: "/producttypen/api/v1",
}
