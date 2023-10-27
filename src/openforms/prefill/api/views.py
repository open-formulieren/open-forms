from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from openforms.api.views import ListMixin

from ..registry import register
from .serializers import (
    ChoiceWrapper,
    PrefillAttributeSerializer,
    PrefillPluginQueryParameterSerializer,
    PrefillPluginSerializer,
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
