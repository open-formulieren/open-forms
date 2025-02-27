from rest_framework import serializers
from zgw_consumers.models import Service

from openforms.api.utils import mark_experimental


@mark_experimental
class ServiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Service
        fields = (
            "url",
            "slug",
            "label",
            "api_root",
            "api_type",
        )
        extra_kwargs = {
            "url": {
                "lookup_field": "pk",
                "view_name": "api:service-detail",
            }
        }
