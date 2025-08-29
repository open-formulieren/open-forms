from rest_framework import serializers

from ..models import AttributeGroup


class AttributeGroupSerializer(serializers.ModelSerializer):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = AttributeGroup
        fields = (
            "uuid",
            "name",
            "description",
        )
