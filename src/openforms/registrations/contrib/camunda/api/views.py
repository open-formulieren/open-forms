from typing import List

from django.utils.translation import gettext_lazy as _

from django_camunda.api import get_process_definitions
from django_camunda.camunda_models import ProcessDefinition
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views

from openforms.utils.api.views import ListMixin

from ..registry import register
from .serializers import CamundaPluginSerializer, ProcessDefinitionSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("List available Camunda process definitions"),
        tags=["registration"],
    ),
)
class ProcessDefinitionListView(ListMixin, views.APIView):
    """
    List the available process definitions & their versions.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ProcessDefinitionSerializer

    @staticmethod
    def get_objects() -> List[ProcessDefinition]:
        return get_process_definitions()


@extend_schema_view(
    get=extend_schema(
        summary=_("List available Camunda plugins"),
        tags=["registration"],
    ),
)
class PluginListView(ListMixin, views.APIView):
    """
    List the Camunda-specific plugins that are registered.

    This endpoint exposes all the plugins that are registered with the Camunda
    registration backend, including non-core plugins.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CamundaPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())
