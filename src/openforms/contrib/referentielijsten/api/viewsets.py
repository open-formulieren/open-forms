from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from requests.exceptions import RequestException
from rest_framework import authentication, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.api.utils import mark_experimental

from ..client import ReferentielijstenClient
from .serializers import ReferentielijstTabellenSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("List tabellen for a Referentielijsten service"),
        description=_(
            "Return a list of available (JSON) tabellen in a given Referentielijsten service configured "
            "in the backend.\n\n"
            "Note that this endpoint is **EXPERIMENTAL**."
        ),
        responses={
            200: ReferentielijstTabellenSerializer(many=True),
        },
    )
)
@mark_experimental
class ReferentielijstenTabellenViewSet(viewsets.ViewSet):
    """
    List tabellen for a given Referentielijst service
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ReferentielijstTabellenSerializer

    @action(detail=False, methods=["get"], url_path="(?P<service_slug>[-a-zA-Z0-9_]+)")
    def get(self, request, service_slug: str | None = None):
        service = get_object_or_404(Service, slug=service_slug)
        try:
            with build_client(
                service, client_factory=ReferentielijstenClient
            ) as client:
                result = client.get_tabellen()
        except RequestException:
            result = []

        assert issubclass(self.serializer_class, serializers.Serializer)
        serializer = self.serializer_class(data=result, many=True)
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)
