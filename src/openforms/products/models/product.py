import uuid as _uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from tinymce.models import HTMLField

from csp_post_processor.fields import CSPPostProcessedWYSIWYGField


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
    name = models.CharField(_("name"), max_length=50)
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        blank=True,
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
    producttype = models.UUIDField(
        _("Producttype"),
        help_text=_("Open Product producttype UUID"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        constraints = [
            # Price field may only be blank when producttype is set
            models.CheckConstraint(
                name="price_not_blank_without_producttype",
                check=(
                    models.Q(producttype__isnull=True, price__isnull=False)
                    | models.Q(
                        producttype__isnull=False,
                        price__isnull=True,
                    )
                ),
                violation_error_message=_(
                    "Price cannot be blank without a producttype."
                ),
            ),
        ]

    def __str__(self):
        return self.name
