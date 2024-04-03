import re
from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, exceptions, permissions, views
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api.views import ListMixin

from ..client import get_objecttypes_client
from ..json_schema import InvalidReference, iter_json_schema_paths, json_schema_matches
from .serializers import (
    ObjecttypeSerializer,
    ObjecttypeVersionSerializer,
    TargetPathsInputSerializer,
    TargetPathsSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["registration"],
    ),
)
class ObjecttypesListView(ListMixin, views.APIView):
    """
    List the available Objecttypes.

    Note that the response data is essentially proxied from the configured Objecttypes API.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ObjecttypeSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        with get_objecttypes_client() as client:
            return client.list_objecttypes()


@extend_schema_view(
    get=extend_schema(
        tags=["registration"],
    ),
)
class ObjecttypeVersionsListView(ListMixin, views.APIView):
    """
    List the available versions for an Objecttype.

    Note that the response data is essentially proxied from the configured Objecttypes API.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ObjecttypeVersionSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        with get_objecttypes_client() as client:
            return client.list_objecttype_versions(self.kwargs["submission_uuid"])


class TargetPathsListView(views.APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)

    @extend_schema(
        request=TargetPathsInputSerializer, responses={200: TargetPathsSerializer}
    )
    def post(self, request: Request, *args: Any, **kwargs: Any):
        input_serializer = TargetPathsInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        # Regex taken from django.urls.converters.UUIDConverter
        match = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$",
            input_serializer.validated_data["objecttype_url"],
        )
        if not match:
            raise exceptions.ValidationError(
                detail={"objecttype_url": _("Invalid URL.")}
            )

        objecttype_uuid = match.group()

        with get_objecttypes_client() as client:

            allow_geometry = client.get_objecttype(objecttype_uuid).get(
                "allowGeometry", True
            )

            _json_schema = client.get_objecttype_version(
                objecttype_uuid, input_serializer.validated_data["objecttype_version"]
            )["jsonSchema"]

        json_schema = {
            "type": "object",
            "properties": {"data": {"type": "object", "properties": _json_schema}},
        }

        if allow_geometry:
            json_schema["properties"]["geometry"] = {"type": "object"}

        return_data = [
            {
                "target_path": json_path.segments,
                "is_required": json_path.required,
                "json_schema": json_schema,
            }
            for json_path, json_schema in iter_json_schema_paths(
                json_schema, fail_fast=False
            )
            if not isinstance(json_schema, InvalidReference)
            if json_schema_matches(
                variable_schema=input_serializer.validated_data["variable_json_schema"],
                target_schema=json_schema,
            )
        ]

        output_serializer = TargetPathsSerializer(many=True, instance=return_data)
        return Response(data=output_serializer.data)
