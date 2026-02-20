from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.config.models.theme import Theme


@extend_schema_serializer(component_name="ThemeV3Serializer")
class ThemeSerializer(serializers.ModelSerializer):
    # Remove the uniqueness constraint as the parent serializer uses `.update_or_create`
    uuid = serializers.UUIDField(validators=[])

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Theme
        fields = (
            "uuid",
            "name",
        )
        extra_kwargs = {
            "uuid": {"read_only": False}  # Overrides the `editable` option on the field
        }
