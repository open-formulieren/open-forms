from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views

from openforms.api.views import ListMixin
from openforms.contrib.zgw.api.views import (
    BaseCatalogueListView,
    BaseDocumentTypesListView,
)

from ..clients import get_objecttypes_client
from .filters import (
    APIGroupQueryParamsSerializer,
    ListDocumentTypesQueryParamsSerializer,
)
from .serializers import (
    ObjectsAPIGroupInputSerializer,
    ObjecttypeSerializer,
    ObjecttypeVersionSerializer,
)

# TODO: https://github.com/open-formulieren/open-forms/issues/611
OBJECTS_API_GROUP_QUERY_PARAMETER = OpenApiParameter(
    name="objects_api_group",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description=_("Identifier of the Objects API group to use."),
)


@extend_schema(
    tags=["contrib"],
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
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
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            return client.list_objecttypes()


@extend_schema(
    tags=["contrib"],
    parameters=[OBJECTS_API_GROUP_QUERY_PARAMETER],
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
        input_serializer = ObjectsAPIGroupInputSerializer(
            data=self.request.query_params
        )
        input_serializer.is_valid(raise_exception=True)

        config_group = input_serializer.validated_data["objects_api_group"]

        with get_objecttypes_client(config_group) as client:
            return client.list_objecttype_versions(self.kwargs["objecttype_uuid"])


@extend_schema_view(
    get=extend_schema(
        summary=_("List available Catalogi from the provided Objects API group"),
        tags=["contrib"],
        parameters=[APIGroupQueryParamsSerializer],
    ),
)
class CatalogueListView(BaseCatalogueListView):
    filter_serializer_class = APIGroupQueryParamsSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_(
            "List the available InformatieObjectTypen from the provided Objects API group"
        ),
        tags=["contrib"],
        parameters=[ListDocumentTypesQueryParamsSerializer],
    ),
)
class DocumentTypesListView(BaseDocumentTypesListView):
    filter_serializer_class = ListDocumentTypesQueryParamsSerializer
