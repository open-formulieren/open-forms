from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, viewsets

from openforms.api import pagination
from openforms.api.utils import mark_experimental
from openforms.forms.api.permissions import FormAPIPermissions

from ..models import ServiceFetchConfiguration
from .renderers import ServiceFetchConfigurationRenderer
from .serializers import ServiceFetchConfigurationSerializer


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
    permission_classes = (FormAPIPermissions,)
    serializer_class = ServiceFetchConfigurationSerializer
    renderer_classes = (ServiceFetchConfigurationRenderer,)

    queryset = ServiceFetchConfiguration.objects.order_by("service", "-pk")
    pagination_class = pagination.PageNumberPagination
