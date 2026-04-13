from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.forms.models import FormVariable

from .service_fetch_config import ServiceFetchConfigurationSerializer


@extend_schema_serializer(component_name="FormVariableV3Serializer")
class FormVariableSerializer(serializers.ModelSerializer):
    service_fetch_configuration = ServiceFetchConfigurationSerializer(
        required=False, allow_null=True
    )
    prefill_options = serializers.JSONField(required=False)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = FormVariable
        fields = (
            "name",
            "key",
            "source",
            "service_fetch_configuration",
            "prefill_plugin",
            "prefill_attribute",
            "prefill_identifier_role",
            "prefill_options",
            "data_type",
            "data_format",
            "is_sensitive_data",
            "initial_value",
        )
