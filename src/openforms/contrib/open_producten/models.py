import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class OpenProductenConfig(SingletonModel):

    producten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Producten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    class Meta:
        verbose_name = _("Open Producten configuration")


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True)

    class Meta:
        abstract = True


class ProductType(models.Model):
    upl_name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        help_text=_("Uniform product name"),
        blank=True,
        null=True,
        editable=False,
    )

    upl_uri = models.URLField(
        verbose_name=_("Url"),
        blank=True,
        null=True,
        editable=False,
        help_text=_("Url to the upn definition."),
    )

    is_deleted = models.BooleanField(
        verbose_name=_("Is deleted"),
        default=False,
        help_text=_(
            "set when the product is deleted in open producten but is linked to existing submission."
        ),
    )

    @property
    def open_producten_price(self):
        now = datetime.date.today()
        return self.prices.filter(valid_from__lte=now).order_by("valid_from").last()

    class Meta:
        abstract = True


class Price(BaseModel):
    product_type = models.ForeignKey(
        "products.Product",
        verbose_name=_("Product type"),
        on_delete=models.CASCADE,
        related_name="prices",
        help_text=_("The product type that this price belongs to"),
    )
    valid_from = models.DateField(
        verbose_name=_("Start date"),
        validators=[MinValueValidator(datetime.date.today)],
        unique=True,
        help_text=_("The date at which this price is valid"),
    )

    class Meta:
        verbose_name = _("Price")
        verbose_name_plural = _("Prices")
        unique_together = ("product_type", "valid_from")

    def __str__(self):
        return f"{self.product_type.upl_name} {self.valid_from}"


class PriceOption(BaseModel):
    price = models.ForeignKey(
        Price,
        verbose_name=_("Price"),
        on_delete=models.CASCADE,
        related_name="options",
        help_text=_("The price this option belongs to"),
    )
    amount = models.DecimalField(
        verbose_name=_("Price"),
        decimal_places=2,
        max_digits=8,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("The amount of the price option"),
    )
    description = models.CharField(
        verbose_name=_("Description"),
        max_length=100,
        help_text=_("Short description of the option"),
    )

    class Meta:
        verbose_name = _("Price option")
        verbose_name_plural = _("Price options")

    def __str__(self):
        return f"{self.description} {self.amount}"
