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
    RegistrationPluginSerializer,
)


@extend_schema_view(
    get=extend_schema(summary=_("List available prefill plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all registration plugins that have been registered.
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
