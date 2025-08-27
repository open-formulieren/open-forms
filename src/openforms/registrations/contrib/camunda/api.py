from django.urls import path
from django.utils.translation import gettext_lazy as _

from django_camunda.api import get_process_definitions
from django_camunda.camunda_models import ProcessDefinition
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers, views

from openforms.api.views import ListMixin


class ProcessDefinitionSerializer(serializers.Serializer):
    id = serializers.CharField()
    key = serializers.CharField(
        help_text=_(
            "The process definition identifier, used to group different versions."
        )
    )
    name = serializers.CharField(
        help_text=_("The human-readable name of the process definition.")
    )
    version = serializers.IntegerField(
        help_text=_("The version identifier relative to the 'key'.")
    )

    class Meta:
        model = ProcessDefinition


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
    def get_objects() -> list[ProcessDefinition]:
        return get_process_definitions()


app_name = "camunda"

urlpatterns = [
    path(
        "process-definitions",
        ProcessDefinitionListView.as_view(),
        name="process-definitions",
    ),
]
