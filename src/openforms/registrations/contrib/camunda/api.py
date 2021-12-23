from typing import List

from django.urls import path
from django.utils.translation import gettext_lazy as _

from django_camunda.api import get_process_definitions
from django_camunda.camunda_models import ProcessDefinition
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views
from zgw_consumers.drf.serializers import APIModelSerializer

from openforms.utils.api.views import ListMixin


class ProcessDefinitionSerializer(APIModelSerializer):
    class Meta:
        model = ProcessDefinition
        fields = ("id", "key", "name", "version")
        extra_kwargs = {
            "key": {
                "help_text": _(
                    "The process definition identifier, used to group different versions."
                ),
            },
            "name": {
                "help_text": _("The human-readable name of the process definition."),
            },
            "version": {
                "help_text": _("The version identifier relative to the 'key'."),
            },
        }


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


app_name = "camunda"

urlpatterns = [
    path(
        "process-definitions",
        ProcessDefinitionListView.as_view(),
        name="process-definitions",
    ),
]
