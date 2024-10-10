from rest_framework import serializers

from openforms.products.models import Product as ProductType

from ..models import Price, PriceOption


class PriceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceOption
        exclude = ("price",)


class PriceSerializer(serializers.ModelSerializer):
    options = PriceOptionSerializer(many=True)

    class Meta:
        model = Price
        fields = "__all__"


class ProductTypeSerializer(serializers.ModelSerializer):
    open_producten_price = PriceSerializer()

    class Meta:
        model = ProductType
        exclude = ("id", "information", "price")
