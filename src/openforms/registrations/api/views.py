from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..constants import RegistrationAttribute
from ..registry import register
from .serializers import AttributeSerializer, ChoiceWrapper, PluginSerializer


# TODO use shared mixin from utils app in other PR
class ListMixin:
    def get_serializer(self, **kwargs):
        return self.serializer_class(
            many=True,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    def get(self, request, *args, **kwargs):
        objects = self.get_objects()
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(summary=_("List available prefill plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all registration plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PluginSerializer

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
    serializer_class = AttributeSerializer

    def get_objects(self):
        choices = RegistrationAttribute.choices

        return [ChoiceWrapper(choice) for choice in choices]
