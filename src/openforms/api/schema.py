from collections.abc import Mapping

from django.utils.translation import gettext_lazy as _

from drf_spectacular.openapi import AutoSchema as _AutoSchema
from drf_spectacular.plumbing import force_instance
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers, status
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings


class AutoSchema(_AutoSchema):
    # Subclassed because we often end up hooking into the schema generator. This
    # provides the plumbing.

    def get_override_parameters(self):
        params = super().get_override_parameters()

        if self._is_create_operation() and self.serializer_has_url_field():
            params = params + [
                OpenApiParameter(
                    name="Location",
                    type=str,
                    location=OpenApiParameter.HEADER,
                    description=_("URL of the newly created resource."),
                    response=[status.HTTP_201_CREATED],
                    required=True,
                )
            ]

        return params

    def serializer_has_url_field(self) -> bool:
        serializer = force_instance(self.get_response_serializers())
        if not isinstance(serializer, Serializer | ListSerializer):
            return False
        fields: Mapping[str, serializers.Field] = serializer.fields
        return api_settings.URL_FIELD_NAME in fields
