from typing import TypedDict

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.forms.models.category import Category


@extend_schema_serializer(component_name="CategoryV3Serializer")
class CategorySerializer(serializers.ModelSerializer):
    # Remove the uniqueness constraint as the parent serializer uses `.update_or_create`
    uuid = serializers.UUIDField(validators=[])
    ancestors = serializers.SerializerMethodField(read_only=True)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Category
        fields = (
            "name",
            "uuid",
            "ancestors",
            "depth",
        )

    class NameUUID(TypedDict):
        name: str
        uuid: str

    def get_ancestors(self, obj) -> list[NameUUID]:
        ancestors = obj.get_ancestors()
        return [{"uuid": str(n.uuid), "name": n.name} for n in ancestors]
