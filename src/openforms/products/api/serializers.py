from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..models import Product


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    producttype = serializers.UUIDField(
        source="producttype_uuid",
        label=_("Producttype ID"),
        help_text=_("Open Product producttype UUID."),
        allow_null=True,
    )

    class Meta:
        model = Product
        fields = (
            "url",
            "uuid",
            "name",
            "url",
            "price",
            "information",
            "producttype",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:product-detail",
                "lookup_field": "uuid",
            },
        }
