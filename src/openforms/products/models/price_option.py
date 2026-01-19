from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.products.models import Product


class PriceOption(models.Model):
    price_option_uuid = models.UUIDField(
        _("price option UUID"),
        help_text=_("Unique identifier of the original Open Product price option"),
        unique=True,
        null=True,
        blank=True,
    )
    name = models.CharField(_("name"), max_length=50)
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    product = models.ForeignKey(
        Product, related_name="price_options", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
