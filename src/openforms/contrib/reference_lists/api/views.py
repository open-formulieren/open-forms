from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from requests.exceptions import RequestException
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.api.views import ListMixin

from ..client import ReferenceListsClient, Table, TableItem
from .serializers import (
    ReferenceListsTableItemSerializer,
    ReferenceListsTableSerializer,
)


@extend_schema(
    summary=_("List tables for a ReferenceLists service"),
)
class ReferenceListsTablesViewSet(ListMixin, APIView):
    """
    Return a list of available tables in a given ReferenceLists service configured in the backend.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ReferenceListsTableSerializer

    def get_objects(self) -> list[Table]:
        service = get_object_or_404(Service, slug=self.kwargs["service_slug"])

        try:
            with build_client(service, client_factory=ReferenceListsClient) as client:
                result = client.get_all_tables()
        except RequestException:
            result = []

        return result


@extend_schema(
    summary=_("List items for a ReferenceLists table"),
)
class ReferenceListsTableItemsViewSet(ListMixin, APIView):
    """
    Return a list of available items in a given ReferenceLists table.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ReferenceListsTableItemSerializer

    def get_objects(self) -> list[TableItem]:
        service = get_object_or_404(Service, slug=self.kwargs["service_slug"])

        try:
            with build_client(service, client_factory=ReferenceListsClient) as client:
                result = client.get_items_for_table_cached(self.kwargs["table_code"])
        except RequestException:
            result = []

        return result
