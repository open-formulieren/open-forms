from rest_framework import serializers

from ..models import ServiceFetchConfiguration


class ServiceFetchConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFetchConfiguration
        fields = (
            "service",
            "path",
            "method",
            "headers",
            "query_params",
            "body",
            "data_mapping_type",
            "mapping_expression",
        )
