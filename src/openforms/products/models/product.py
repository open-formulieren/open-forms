from django.db import models


class Product(models.Model):
    """
    Product model for a PDC (Producten en Diensten Catalogus) definition.
    """
    name = models.CharField(max_length=50)
    url = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
