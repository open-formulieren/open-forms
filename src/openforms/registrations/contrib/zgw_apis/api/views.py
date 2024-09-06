from dataclasses import dataclass, field

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.api.views.mixins import ListMixin
from openforms.contrib.zgw.api.serializers import CaseTypeSerializer
from openforms.contrib.zgw.api.views import (
    BaseCatalogueListView,
    BaseInformatieObjectTypenListView,
)

from .filters import (
    APIGroupQueryParamsSerializer,
    ListCaseTypesQueryParamsSerializer,
    ListInformatieObjectTypenQueryParamsSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List the available Catalogi from the provided ZGW API group"),
        parameters=[APIGroupQueryParamsSerializer],
    ),
)
class CatalogueListView(BaseCatalogueListView):
    filter_serializer_class = APIGroupQueryParamsSerializer


@dataclass
class CaseType:
    identification: str
    # different versions could have different descriptions
    description: str = field(compare=False)
    # different versions may have different publication states
    is_published: bool = field(compare=False)


@extend_schema_view(
    get=extend_schema(
        summary=_("List the available case types within a catalogue (ZGW APIs)"),
        parameters=[ListCaseTypesQueryParamsSerializer],
    ),
)
class CaseTypesListView(ListMixin[CaseType], APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CaseTypeSerializer

    def get_objects(self):
        filter_serializer = ListCaseTypesQueryParamsSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        catalogue_url = filter_serializer.validated_data["catalogue_url"]

        case_types: list[CaseType] = []
        with filter_serializer.get_ztc_client() as client:
            for ct in client.get_all_case_types(catalogus=catalogue_url):
                case_type = CaseType(
                    identification=ct["identificatie"],
                    description=ct["omschrijving"],
                    is_published=not ct.get("concept", False),
                )
                if case_type in case_types:
                    continue
                case_types.append(case_type)

        return case_types


@extend_schema_view(
    get=extend_schema(
        summary=_(
            "List the available InformatieObjectTypen from the provided ZGW API group"
        ),
        parameters=[ListInformatieObjectTypenQueryParamsSerializer],
    ),
)
class InformatieObjectTypenListView(BaseInformatieObjectTypenListView):
    filter_serializer_class = ListInformatieObjectTypenQueryParamsSerializer
