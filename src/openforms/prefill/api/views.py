from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from openforms.api.views import ListMixin
from openforms.registrations.contrib.objects_api.api.serializers import (
    ObjectsAPIGroupInputSerializer,
)
from openforms.registrations.contrib.objects_api.client import get_objecttypes_client

from ..registry import register
from .serializers import (
    ChoiceWrapper,
    PrefillAttributeSerializer,
    PrefillObjectsAPIAttributeSerializer,
    PrefillObjectsAPIObjecttypeSerializer,
    PrefillObjectsAPIObjecttypeVersionSerializer,
    PrefillPluginQueryParameterSerializer,
    PrefillPluginSerializer,
)

OBJECTS_API_GROUP_QUERY_PARAMETER = OpenApiParameter(
    name="objects_api_group",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description=_("Which Objects API group to use."),
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List available prefill plugins"),
        parameters=[*PrefillPluginQueryParameterSerializer.as_openapi_params()],
    ),
)
class PluginListView(ListMixin, APIView):
    """
    List all prefill plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillPluginSerializer

    def get_objects(self):
        query_param_serializer = PrefillPluginQueryParameterSerializer(
            data=self.request.query_params
        )
        if not query_param_serializer.is_valid(raise_exception=False):
            return []

        plugins = register.iter_enabled_plugins()
        for_component = query_param_serializer.validated_data.get("component_type")
        if not for_component:
            return plugins
        return [plugin for plugin in plugins if for_component in plugin.for_components]


@extend_schema_view(
    get=extend_schema(summary=_("List available attributes")),
)
class PluginAttributesListView(ListMixin, APIView):
    """
    List the available prefill attributes for a given plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillAttributeSerializer

    def get_objects(self):
        try:
            plugin = register[self.kwargs["plugin"]]
        except KeyError:
            raise NotFound(
                detail=_("No plugin with ID '{plugin}' found").format(**self.kwargs)
            )
        choices = plugin.get_available_attributes()

        return [ChoiceWrapper(choice) for choice in choices]


@extend_schema_view(
    get=extend_schema(summary=_("List available objecttypes for Objects API")),
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
)
class PluginObjectsAPIObjecttypeListView(ListMixin, APIView):
    """
    List the available prefill objecttypes for Objects API plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillObjectsAPIObjecttypeSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            return client.list_objecttypes()


@extend_schema_view(
    get=extend_schema(summary=_("List available objecttype versions for Objects API")),
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
)
class PluginObjectsAPIObjecttypeVersionListView(ListMixin, APIView):
    """
    List the available prefill objecttype versions for Objects API plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillObjectsAPIObjecttypeVersionSerializer

    def get_objects(self):
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]
        objecttype_uuid = self.kwargs["objects_api_objecttype_uuid"]

        with get_objecttypes_client(config_group) as client:
            return client.list_objecttype_versions(objecttype_uuid)


@extend_schema_view(
    get=extend_schema(summary=_("List available attributes for Objects API")),
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
)
class PluginObjectsAPIAttributesListView(ListMixin, APIView):
    """
    List the available attributes for Objects API plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillObjectsAPIAttributeSerializer

    def get_objects(self):
        plugin = register["objects_api"]
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]
        choices = plugin.get_available_attributes(
            reference={
                "objects_api_group": config_group,
                "objects_api_objecttype_uuid": self.kwargs[
                    "objects_api_objecttype_uuid"
                ],
                "objects_api_objecttype_version": self.kwargs[
                    "objects_api_objecttype_version"
                ],
            }
        )

        return choices
