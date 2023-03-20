from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, viewsets
from rest_framework.views import APIView

from openforms.api import pagination
from openforms.api.serializers import ExceptionSerializer
from openforms.api.utils import mark_experimental
from openforms.api.views import ListMixin
from openforms.forms.api.serializers import FormVariableSerializer

from .api.serializers import ServiceFetchConfigurationSerializer
from .models import ServiceFetchConfiguration
from .service import get_static_variables


@extend_schema_view(
    get=extend_schema(
        summary=_("Get static data"),
        description=_("List the static data that will be associated with every form"),
        responses={
            200: FormVariableSerializer(many=True),
            403: ExceptionSerializer,
        },
    ),
)
class StaticFormVariablesView(ListMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = FormVariableSerializer

    def get_objects(self):
        return get_static_variables()


@extend_schema_view(
    list=extend_schema(
        summary=_("List available service fetch configurations"),
        description=_(
            "Return a list of available services fetch configurations configured "
            "in the backend.\n\n"
            "Note that this endpoint is **EXPERIMENTAL**."
        ),
    )
)
@mark_experimental
class ServiceFetchConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ServiceFetchConfigurationSerializer

    queryset = ServiceFetchConfiguration.objects.all().order_by("service")
    pagination_class = pagination.PageNumberPagination
