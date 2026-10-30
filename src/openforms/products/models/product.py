import uuid as _uuid
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from tinymce.models import HTMLField

from csp_post_processor.fields import CSPPostProcessedWYSIWYGField
from openforms.typing import StrOrPromise

from ..constants import ProductSourceChoices


class Product(models.Model):
    """
    Product model for a PDC (Producten en Diensten Catalogus) definition.
    """

    uuid = models.UUIDField(
        _("UUID"),
        default=_uuid.uuid4,
        help_text=_("Globally unique identifier"),
        unique=True,
    )
    product_source = models.CharField(
        _("Product source"),
        choices=ProductSourceChoices.choices,
        default=ProductSourceChoices.local,
        help_text=_(
            "The available types of the product. It can be a local product "
            "created in the admin interface or an external one."
        ),
    )
    name = models.CharField(_("name"), max_length=50)
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        null=True,
    )

    information = CSPPostProcessedWYSIWYGField(
        HTMLField(
            verbose_name=_("information"),
            blank=True,
            help_text=_(
                "Information text to be displayed in the confirmation page and confirmation email."
            ),
        ),
    )

    #
    # Open Product related fields
    #
    producttype_uuid = models.UUIDField(
        _("Producttype ID"),
        help_text=_("Open Product producttype UUID."),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        constraints = [
            # Price field may only be blank when producttype is set
            models.CheckConstraint(
                name="price_required_without_producttype_uuid",
                condition=(
                    models.Q(
                        product_source=ProductSourceChoices.local,
                        producttype_uuid__isnull=True,
                        price__isnull=False,
                    )
                    | (
                        ~models.Q(product_source=ProductSourceChoices.local)
                        & models.Q(
                            producttype_uuid__isnull=False,
                            price__isnull=True,
                        )
                    )
                ),
                violation_error_message=_(
                    "Price cannot be blank and can only be set for local products "
                    "and without a producttype ID."
                ),
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self) -> None:
        errors: dict[str, list[StrOrPromise]] = defaultdict(list)
        if self.product_source == ProductSourceChoices.local and not self.price:
            errors["price"].append(_("Price is required for local products."))

        if errors:
            raise ValidationError(errors)
