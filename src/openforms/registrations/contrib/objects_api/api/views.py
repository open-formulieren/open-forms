import re
from typing import Any

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views

from openforms.api.views import ListMixin
from openforms.forms.models import FormRegistrationBackend, FormVariable

from ..client import get_objecttypes_client
from ..json_schema import InvalidReference, iter_json_schema_paths
from .serializers import (
    ObjecttypeSerializer,
    ObjecttypeVersionSerializer,
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


@extend_schema_view(
    get=extend_schema(
        tags=["registration"],
        parameters=[
            OpenApiParameter(
                name="form_uuid",
                required=True,
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=_("UUID of the form"),
            ),
            OpenApiParameter(
                name="backend_key",
                required=True,
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=_("Key of the registration backend"),
            ),
            OpenApiParameter(
                name="variable_key",
                required=True,
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=_("Key of the variable"),
            ),
        ],
    ),
)
class TargetPathsListView(ListMixin, views.APIView):
    """
    List the available target paths for an Objects API registration plugin, compatible with the provided variable key.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = TargetPathsSerializer

    def get_objects(self) -> list[dict[str, Any]]:

        form_uuid = self.request.query_params["form_uuid"]

        registration_backend = get_object_or_404(
            FormRegistrationBackend,
            form__uuid=form_uuid,
            key=self.request.query_params["backend_key"],
            options__version=2,
        )
        variable_key = self.request.query_params["variable_key"]
        form_variable = get_object_or_404(
            FormVariable,
            form__uuid=form_uuid,
            key=variable_key,
        )

        with get_objecttypes_client() as client:
            # Regex taken from django.urls.converters.UUIDConverter
            objecttype_uuid = re.search(
                r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$",
                registration_backend.options["objecttype"],
            ).group()

            json_schema = client.get_objecttype_version(
                objecttype_uuid, registration_backend.options["objecttype_version"]
            )["jsonSchema"]

        return [
            {
                "target_path": json_path.segments,
                "required": json_path.required,
                json_schema: json_schema,
            }
            for json_path, json_schema in iter_json_schema_paths(
                json_schema, fail_fast=False
            )
            if not isinstance(json_schema, InvalidReference)
            if form_variable.matches_json_schema(json_schema)
        ]
