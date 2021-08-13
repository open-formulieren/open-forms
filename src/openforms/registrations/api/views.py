from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from ...utils.api.views import ListMixin
from ..constants import RegistrationAttribute
from ..registry import register
from .serializers import (
    ChoiceWrapper,
    RegistrationAttributeSerializer,
    RegistrationPluginOptionsSchemaSerializer,
    RegistrationPluginSerializer,
)


@extend_schema_view(
    get=extend_schema(summary=_("List available registration plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all available registration plugins.

    Registration plugins are responsible for the implementation details to register the form submission
    with various backends, such as "API's voor zaakgericht werken", StUF-ZDS and others.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegistrationPluginSerializer

    def get_objects(self):
        return list(register)


@extend_schema_view(
    get=extend_schema(summary=_("List available registration attributes")),
)
class AllAttributesListView(ListMixin, APIView):
    """
    List the available registration attributes.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegistrationAttributeSerializer

    def get_objects(self):
        choices = RegistrationAttribute.choices

        return [ChoiceWrapper(choice) for choice in choices]


@extend_schema_view(
    get=extend_schema(summary=_("List the plugin configuration options form schemas"))
)
class PluginsConfigurationOptionsView(ListMixin, APIView):
    """
    Retrieve the JSON schema of each plugin's configuration options.

    The JSON schema can be used to generate a configuration form matching the
    available options.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegistrationPluginOptionsSchemaSerializer

    def get_objects(self):
        return register
