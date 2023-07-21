from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..base import Location, Product


class ProductIDField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label", _("Product ID"))
        super().__init__(*args, **kwargs)

    def run_validation(self, data) -> Product:
        """
        Normalize to dataclass instance.
        """
        value = super().run_validation(data)
        return Product(identifier=value, code="", name="")


class LocationIDField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label", _("Location ID"))
        super().__init__(*args, **kwargs)

    def run_validation(self, data) -> Location:
        """
        Normalize to dataclass instance.
        """
        value = super().run_validation(data)
        return Location(identifier=value, name="")
