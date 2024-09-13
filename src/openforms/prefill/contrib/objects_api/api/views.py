from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import authentication, permissions, views

from openforms.api.views import ListMixin
from openforms.contrib.objects_api.api.serializers import ObjectsAPIGroupInputSerializer
from openforms.contrib.objects_api.clients import get_objecttypes_client
from openforms.contrib.objects_api.json_schema import (
    InvalidReference,
    iter_json_schema_paths,
)

from .serializers import PrefillTargetPathsSerializer

OBJECTS_API_GROUP_QUERY_PARAMETER = OpenApiParameter(
    name="objects_api_group",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description=_("Which Objects API group to use."),
)


@extend_schema(
    summary=_("List available attributes for Objects API"),
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
)
class ObjecttypePropertiesListView(ListMixin, views.APIView):
    """
    List the available JSON properties defined on a particular objecttype.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillTargetPathsSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            json_schema = client.get_objecttype_version(
                self.kwargs["objecttype_uuid"],
                self.kwargs["objecttype_version"],
            )["jsonSchema"]

        return [
            {
                "target_path": json_path.segments,
                "json_schema": json_schema,
            }
            for json_path, json_schema in iter_json_schema_paths(
                json_schema, fail_fast=False
            )
            if not isinstance(json_schema, InvalidReference)
            if not len(json_path.segments) == 0
        ]
