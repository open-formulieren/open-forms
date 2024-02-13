from typing import Any

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views

from openforms.api.views import ListMixin

from ..client import get_objecttypes_client
from .serializers import ObjecttypeSerializer, ObjecttypeVersionSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["registration"],
    ),
)
class ObjecttypesListView(ListMixin, views.APIView):
    """
    List the available Objecttypes.

    Note that the response data is essentially proxied from the configured Objecttypes API.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ObjecttypeSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        with get_objecttypes_client() as client:
            return client.list_objecttypes()


@extend_schema_view(
    get=extend_schema(
        tags=["registration"],
    ),
)
class ObjecttypeVersionsListView(ListMixin, views.APIView):
    """
    List the available versions for an Objecttype.

    Note that the response data is essentially proxied from the configured Objecttypes API.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ObjecttypeVersionSerializer

    def get_objects(self) -> list[dict[str, Any]]:
        with get_objecttypes_client() as client:
            return client.list_objecttype_versions(self.kwargs["submission_uuid"])
