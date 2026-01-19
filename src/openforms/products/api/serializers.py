from rest_framework import serializers

from ..models import Product


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = (
            "url",
            "uuid",
            "name",
            "url",
            "price_options",
            "information",
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
