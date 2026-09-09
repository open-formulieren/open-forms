import uuid

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.validators import ModelValidator

from ..models import ServiceFetchConfiguration
from ..validators import validate_mapping_expression, validate_request_body


class ServiceFetchConfigurationSerializer(serializers.HyperlinkedModelSerializer):
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

    # only exists to deal with the frontend code nightmare that's split between v2 and
    # v3, as we clean up the code there...
    service_uuid = serializers.SerializerMethodField()

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
            "service_uuid",
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
        extra_kwargs = {
            "service": {
                "lookup_field": "pk",
                "view_name": "api:service-detail",
            },
        }

    def get_service_uuid(self, obj: ServiceFetchConfiguration) -> uuid.UUID:
        return obj.service.uuid
