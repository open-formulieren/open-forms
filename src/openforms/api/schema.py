from django.utils.translation import gettext_lazy as _

from drf_spectacular.openapi import AutoSchema as _AutoSchema
from drf_spectacular.plumbing import force_instance
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.settings import api_settings


class AutoSchema(_AutoSchema):
    # Subclassed because we often end up hooking into the schema generator. This
    # provides the plumbing.

    def get_override_parameters(self):
        params = super().get_override_parameters()

        if self._is_create_operation() and self._serializer_has_url_field():
            params = params + [
                OpenApiParameter(
                    name="Location",
                    type=str,
                    location=OpenApiParameter.HEADER,
                    description=_("URL of the newly created resource."),
                    response=[status.HTTP_201_CREATED],
                    required=False,
                )
            ]

        return params

    def _serializer_has_url_field(self) -> bool:
        from rest_framework.serializers import ListSerializer, Serializer

        serializer = force_instance(self.get_response_serializers())
        # Only plain Serializer instances have a fields mapping; ListSerializer,
        # BaseSerializer and Field subclasses do not.
        if not isinstance(serializer, Serializer) or isinstance(
            serializer, ListSerializer
        ):
            return False
        fields: dict = getattr(serializer, "fields", {})
        return api_settings.URL_FIELD_NAME in fields
