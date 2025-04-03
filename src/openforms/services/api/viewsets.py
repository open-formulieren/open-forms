from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions, viewsets
from zgw_consumers.models import Service

from openforms.api.utils import mark_experimental
from openforms.config.models import GlobalConfiguration

from . import serializers


@extend_schema_view(
    list=extend_schema(
        summary=_("List available services"),
        description=_(
            "Return a list of available (JSON) services/registrations configured "
            "in the backend.\n\n"
            "Note that this endpoint is **EXPERIMENTAL**."
        ),
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                description=_("The type of Services to return."),
                required=False,
                enum=["reference_lists"],
            )
        ],
    ),
)
@mark_experimental
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Configured Services
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.ServiceSerializer

    queryset = Service.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("type") == "reference_lists":
            config = GlobalConfiguration.get_solo()
            return config.reference_lists_services
        return qs
