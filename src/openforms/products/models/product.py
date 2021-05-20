from django.db import models
from django.utils.translation import ugettext_lazy as _


class Product(models.Model):
    """
    Product model for a PDC (Producten en Diensten Catalogus) definition.
    """

    name = models.CharField(_("name"), max_length=50)
    url = models.TextField(_("URL"), blank=True)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
