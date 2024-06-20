import re
from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import authentication, exceptions, permissions, views
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api.views import ListMixin

from ..client import get_objecttypes_client
from ..json_schema import InvalidReference, iter_json_schema_paths, json_schema_matches
from .serializers import (
    ObjectsAPIGroupInputSerializer,
    ObjecttypeSerializer,
    ObjecttypeVersionSerializer,
    TargetPathsInputSerializer,
    TargetPathsSerializer,
)

# TODO: https://github.com/open-formulieren/open-forms/issues/611
OBJECTS_API_GROUP_QUERY_PARAMETER = OpenApiParameter(
    name="objects_api_group",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description=_("Which Objects API group to use."),
)


@extend_schema(
    tags=["registration"],
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
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
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            return client.list_objecttypes()


@extend_schema(
    tags=["registration"],
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
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
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
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

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            json_schema = client.get_objecttype_version(
                objecttype_uuid, input_serializer.validated_data["objecttype_version"]
            )["jsonSchema"]

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
