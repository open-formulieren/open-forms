from rest_framework import serializers

from openforms.products.models.price_option import PriceOption

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
            "price_options": {
                "view_name": "api:priceoption-detail",
                "lookup_field": "price_option_uuid",
            },
        }


class PriceOptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PriceOption
        fields = (
            "url",
            "price_option_uuid",
            "name",
            "price",
            "product",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "product": {
                "view_name": "api:product-detail",
                "lookup_field": "uuid",
            },
        }
