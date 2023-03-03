from rest_framework import serializers
from zgw_consumers.models import Service

from openforms.api.utils import mark_experimental


@mark_experimental
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "label",
            "api_root",
            "api_type",
        )
