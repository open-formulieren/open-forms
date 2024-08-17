from dataclasses import dataclass, field
from typing import ClassVar

from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.api.views import ListMixin

from .filters import DocumentTypesFilter, ProvidesCatalogiClientQueryParamsSerializer
from .serializers import CatalogueSerializer, InformatieObjectTypeSerializer


@dataclass
class Catalogue:
    url: str
    domain: str
    rsin: str
    name: str = ""

    @property
    def label(self) -> str:
        return self.name or f"{self.domain} (RSIN: {self.rsin})"


class BaseCatalogueListView(ListMixin[Catalogue], APIView):
    """
    List the available catalogues.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CatalogueSerializer
    filter_serializer_class: ClassVar[type[ProvidesCatalogiClientQueryParamsSerializer]]

    def get_objects(self):
        params = self.request.query_params
        filter_serializer = self.filter_serializer_class(data=params)
        filter_serializer.is_valid(raise_exception=True)

        with filter_serializer.get_ztc_client() as client:
            catalogus_data = client.get_all_catalogi()

        return [
            Catalogue(
                url=item["url"],
                domain=item["domein"],
                rsin=item["rsin"],
                name=item.get("naam", ""),
            )
            for item in catalogus_data
        ]


@dataclass
class DocumentType:
    catalogue: Catalogue
    omschrijving: str
    url: str = field(compare=False)  # different versions have different URLs
    is_published: bool = field(
        compare=False
    )  # different versions may have different publication states

    def catalogus_label(self) -> str:
        return self.catalogue.label


class BaseInformatieObjectTypenListView(ListMixin[DocumentType], APIView):
    """
    List the available InformatieObjectTypen.

    Each InformatieObjectType is uniquely identified by its 'omschrijving', 'catalogus',
    and beginning and end date. If multiple same InformatieObjectTypen exist for different dates,
    only one entry is returned.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeSerializer
    filter_serializer_class: ClassVar[type[DocumentTypesFilter]]

    def get_objects(self) -> list[DocumentType]:
        filter_serializer = self.filter_serializer_class(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        catalogus_url = filter_serializer.validated_data["catalogus_url"]

        document_types: list[DocumentType] = []
        with filter_serializer.get_ztc_client() as client:
            # look up the relevant catalogue information, since we need to embed
            # information in the document types for the formio-builder file component.
            _catalogues: list[dict]
            if catalogus_url:
                response = client.get(catalogus_url)
                response.raise_for_status()
                _catalogues = [response.json()]
            else:
                _catalogues = list(client.get_all_catalogi())

            catalogues: dict[str, Catalogue] = {
                item["url"]: Catalogue(
                    url=item["url"],
                    domain=item["domein"],
                    rsin=item["rsin"],
                    name=item.get("naam", ""),
                )
                for item in _catalogues
            }

            # now, look up the document types, possibly filtered
            for iotype in client.get_all_informatieobjecttypen(catalogus=catalogus_url):
                document_type = DocumentType(
                    url=iotype["url"],
                    omschrijving=iotype["omschrijving"],
                    catalogue=catalogues[iotype["catalogus"]],
                    is_published=not iotype.get("concept", False),
                )
                if document_type in document_types:
                    continue
                document_types.append(document_type)

        return document_types
