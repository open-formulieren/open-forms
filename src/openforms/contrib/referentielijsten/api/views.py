from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from requests.exceptions import RequestException
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.api.views import ListMixin

from ..client import ReferentielijstenClient, Tabel
from .serializers import ReferentielijstTabellenSerializer


@extend_schema(
    summary=_("List tabellen for a Referentielijsten service"),
)
class ReferentielijstenTabellenViewSet(ListMixin, APIView):
    """
    Return a list of available tabellen in a given Referentielijsten service configured in the backend.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ReferentielijstTabellenSerializer

    def get_objects(self) -> list[Tabel]:
        service = get_object_or_404(Service, slug=self.kwargs["service_slug"])

        try:
            with build_client(
                service, client_factory=ReferentielijstenClient
            ) as client:
                result = client.get_tabellen()
        except RequestException:
            result = []

        return result
