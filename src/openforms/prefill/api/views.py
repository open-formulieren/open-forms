from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from openforms.utils.api.views import ListMixin

from ..registry import register
from .serializers import (
    ChoiceWrapper,
    PrefillAttributeSerializer,
    PrefillPluginSerializer,
)


@extend_schema_view(
    get=extend_schema(summary=_("List available prefill plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all prefill plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PrefillPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


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
