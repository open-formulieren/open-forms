from rest_framework import serializers

from ..models import ServiceFetchConfiguration
from ..validators import ServiceFetchConfigurationValidator


class ServiceFetchConfigurationSerializer(serializers.ModelSerializer):
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
            "service",
            "path",
            "method",
            "headers",
            "query_params",
            "body",
            "data_mapping_type",
            "mapping_expression",
        )
        validators = [ServiceFetchConfigurationValidator()]
