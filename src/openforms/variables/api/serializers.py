from rest_framework import serializers

from openforms.api.validators import ModelValidator

from ..models import ServiceFetchConfiguration
from ..validators import validate_mapping_expression, validate_request_body


class ServiceFetchConfigurationSerializer(serializers.HyperlinkedModelSerializer):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # add id for the bulk update of form_variables
        # even though this is in Meta.fields, it won't get passed otherwise
        if "id" in data:
            value["id"] = data["id"]

        return value

    class Meta:
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
        )
        validators = [
            ModelValidator[ServiceFetchConfiguration](validate_mapping_expression),
            ModelValidator[ServiceFetchConfiguration](validate_request_body),
        ]
        extra_kwargs = {
            "service": {
                "lookup_field": "pk",
                "view_name": "api:service-detail",
            },
        }
