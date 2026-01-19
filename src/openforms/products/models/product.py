import uuid as _uuid

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
    product_type_uuid = models.UUIDField(
        _("product type UUID"),
        blank=True,
        null=True,
        unique=True,
        editable=False,
        help_text=_(
            "Unique identifier of the product type (originates from Open Product)."
        ),
    )
    name = models.CharField(_("name"), max_length=50)

    information = CSPPostProcessedWYSIWYGField(
        HTMLField(
            verbose_name=_("information"),
            blank=True,
            help_text=_(
                "Information text to be displayed in the confirmation page and confirmation email."
            ),
        ),
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.name
