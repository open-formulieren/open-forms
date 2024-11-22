from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import authentication, permissions, views
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.contrib.objects_api.clients import get_objecttypes_client
from openforms.contrib.objects_api.json_schema import (
    InvalidReference,
    iter_json_schema_paths,
    json_schema_matches,
)

from .serializers import TargetPathsInputSerializer, TargetPathsSerializer


class TargetPathsListView(views.APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)

    @extend_schema(
        request=TargetPathsInputSerializer, responses={200: TargetPathsSerializer}
    )
    def post(self, request: Request, *args: Any, **kwargs: Any):
        input_serializer = TargetPathsInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            json_schema = client.get_objecttype_version(
                input_serializer.validated_data["objecttype"],
                input_serializer.validated_data["objecttype_version"],
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
            if json_path.segments
        ]

        output_serializer = TargetPathsSerializer(many=True, instance=return_data)
        return Response(data=output_serializer.data)
