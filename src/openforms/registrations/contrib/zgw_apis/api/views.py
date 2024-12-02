from dataclasses import dataclass, field

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.api.views.mixins import ListMixin
from openforms.contrib.zgw.api.serializers import (
    CaseTypeProductSerializer,
    CaseTypeSerializer,
    RoleTypeSerializer,
)
from openforms.contrib.zgw.api.views import (
    BaseCatalogueListView,
    BaseDocumentTypesListView,
)
from openforms.contrib.zgw.products_and_services import resolve_case_type_products
from openforms.utils.date import datetime_in_amsterdam

from .filters import (
    APIGroupQueryParamsSerializer,
    FilterForCaseTypeQueryParamsSerializer,
    ListCaseTypesQueryParamsSerializer,
    ListDocumentTypesQueryParamsSerializer,
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
        summary=_("List the available document types from the provided ZGW API group"),
        parameters=[ListDocumentTypesQueryParamsSerializer],
    ),
)
class DocumentTypesListView(BaseDocumentTypesListView):
    filter_serializer_class = ListDocumentTypesQueryParamsSerializer


@dataclass
class RoleType:
    description: str
    description_generic: str


@extend_schema_view(
    get=extend_schema(
        summary=_(
            "List the available role types bound to a case type within a catalogue "
            "(ZGW APIs)"
        ),
        parameters=[FilterForCaseTypeQueryParamsSerializer],
    ),
)
class RoleTypeListView(ListMixin[RoleType], APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RoleTypeSerializer

    def get_objects(self) -> list[RoleType]:
        filter_serializer = FilterForCaseTypeQueryParamsSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        catalogue_url = filter_serializer.validated_data["catalogue_url"]
        case_type_identification = filter_serializer.validated_data[
            "case_type_identification"
        ]
        role_types: list[RoleType] = []
        with filter_serializer.get_ztc_client() as client:
            _role_types = client.get_all_role_types(
                catalogus=catalogue_url,
                within_casetype=case_type_identification,
            )
        for _role_type in _role_types:
            # skip over initiator, since that one is set automatically and there can
            # only be one
            if (
                description_generic := _role_type["omschrijvingGeneriek"]
            ) == "initiator":
                continue
            role_type = RoleType(
                description=_role_type["omschrijving"],
                description_generic=description_generic,
            )
            if role_type not in role_types:
                role_types.append(role_type)
        return role_types


@dataclass
class Product:
    url: str
    description: str = ""


@extend_schema_view(
    get=extend_schema(
        summary=_(
            "List the available products bound to a case type within a catalogue (ZGW APIs)"
        ),
        parameters=[FilterForCaseTypeQueryParamsSerializer],
    ),
)
class ProductsListView(ListMixin[Product], APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CaseTypeProductSerializer

    def get_objects(self):
        filter_serializer = FilterForCaseTypeQueryParamsSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        catalogue_url = filter_serializer.validated_data["catalogue_url"]
        case_type_identification = filter_serializer.validated_data[
            "case_type_identification"
        ]
        today = datetime_in_amsterdam(timezone.now()).date()

        products: list[Product] = []
        with filter_serializer.get_ztc_client() as client:
            case_type_versions = client.find_case_types(
                catalogus=catalogue_url,
                identification=case_type_identification,
                valid_on=today,
            )
            case_type_products = (
                resolve_case_type_products(case_type_versions)
                if case_type_versions
                else []
            )
            for case_type_product in case_type_products:
                products.append(
                    Product(
                        url=case_type_product["url"],
                        description=case_type_product["description"],
                    )
                )

        return products
