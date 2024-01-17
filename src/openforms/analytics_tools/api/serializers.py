from rest_framework import serializers

from ..models import AnalyticsToolsConfiguration


class AnalyticsToolsConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsToolsConfiguration
        fields = (
            "govmetric_source_id",
            "govmetric_secure_guid",
            "enable_govmetric_analytics",
        )
