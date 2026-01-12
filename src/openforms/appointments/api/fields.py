from collections import Counter

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..base import Location, Product


class ProductIDListField(serializers.ListField):
    child = serializers.CharField(label=_("Product ID"), allow_blank=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label", _("Product IDs"))
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value) -> list[Product]:
        value = super().to_internal_value(value)

        c = Counter(value)
        return [
            Product(identifier=product_id, name="", amount=amount)
            for product_id, amount in c.items()
        ]


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
