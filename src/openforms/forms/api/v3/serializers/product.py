from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.products.models.product import Product


@extend_schema_serializer(component_name="ProductV3Serializer")
class ProductSerializer(serializers.ModelSerializer):
    # Remove the uniqueness validator as the parent serializer uses `.update_or_create`
    uuid = serializers.UUIDField(validators=[])

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Product
        fields = (
            "uuid",
            "name",
            "price",
            "information",
        )
