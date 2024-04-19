from rest_framework import serializers

from ..models import AnalyticsToolsConfiguration


class AnalyticsToolsConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsToolsConfiguration
        fields = (
            "govmetric_source_id_form_finished",
            "govmetric_source_id_form_aborted",
            "govmetric_secure_guid_form_finished",
            "govmetric_secure_guid_form_aborted",
            "enable_govmetric_analytics",
        )
