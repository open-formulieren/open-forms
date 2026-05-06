from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from zgw_consumers.models import Service

from openforms.api.validators import ModelValidator
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.validators import (
    validate_mapping_expression,
    validate_request_body,
)


@extend_schema_serializer(component_name="ServiceFetchConfigurationV3Serializer")
class ServiceFetchConfigurationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    headers = serializers.DictField(
        label=_("HTTP request headers"),
        help_text=_(
            "Additions and overrides for the HTTP request headers as defined in the Service."
        ),
        required=False,
    )
    query_params = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        label=_("HTTP query string"),
        required=False,
    )

    service = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Service.objects.all()
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = ServiceFetchConfiguration
        fields = (
            "id",
            "name",
            "service",
            "path",
            "method",
            "headers",
            "query_params",
            "body",
            "data_mapping_type",
            "mapping_expression",
            "cache_timeout",
        )
        validators = [
            ModelValidator[ServiceFetchConfiguration](validate_mapping_expression),
            ModelValidator[ServiceFetchConfiguration](validate_request_body),
        ]
