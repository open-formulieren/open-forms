from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, viewsets
from zgw_consumers.models import Service

from openforms.api.utils import mark_experimental

from . import serializers


@extend_schema_view(
    list=extend_schema(
        summary=_("List available services"),
        description=_(
            "Return a list of available (JSON) services/registrations configured "
            "in the backend.\n\n"
            "Note that this endpoint is **EXPERIMENTAL**."
        ),
    )
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
