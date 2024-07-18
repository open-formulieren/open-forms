from typing import Any, ClassVar

from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.api.views import ListMixin

from .filters import ProvidesCatalogiClientQueryParamsSerializer
from .serializers import CatalogusSerializer, InformatieObjectTypeSerializer


def _build_catalogus_label(catalogus: dict[str, Any]) -> str:
    return catalogus.get("naam") or f"{catalogus['domein']} (RSIN: {catalogus['rsin']})"


class BaseCatalogiListView(ListMixin, APIView):
    """
    List the available catalogi.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CatalogusSerializer
    filter_serializer_class: ClassVar[type[ProvidesCatalogiClientQueryParamsSerializer]]

    def get_objects(self):
        filter_serializer = self.filter_serializer_class(
            data=self.request.query_params,
        )
        filter_serializer.is_valid(raise_exception=True)

        with filter_serializer.get_ztc_client() as client:
            catalogus_data = client.get_all_catalogi()

        return [
            {
                "domein": catalogus["domein"],
                "rsin": catalogus["rsin"],
                "label": _build_catalogus_label(catalogus),
            }
            for catalogus in catalogus_data
        ]


class BaseInformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen.

    Each InformatieObjectType is uniquely identified by its 'omschrijving', 'catalogus',
    and beginning and end date. If multiple same InformatieObjectTypen exist for different dates,
    only one entry is returned.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeSerializer
    filter_serializer_class: ClassVar[type[ProvidesCatalogiClientQueryParamsSerializer]]

    def get_objects(self):
        filter_serializer = self.filter_serializer_class(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        iotypen_data: dict[tuple[str, str], dict[str, Any]] = {}
        with filter_serializer.get_ztc_client() as client:
            catalogus_data = client.get_all_catalogi()
            catalogus_mapping = {
                catalogus["url"]: catalogus for catalogus in catalogus_data
            }
            catalogus = filter_serializer.validated_data.get("catalogus_url", "")

            for iotype in client.get_all_informatieobjecttypen(catalogus=catalogus):
                # Filter out duplicate entries, as you can set start/end dates on IOTs:
                key = (iotype["catalogus"], iotype["omschrijving"])
                if key not in iotypen_data:
                    iotypen_data[key] = iotype

        iotypen = []

        for iotype in iotypen_data.values():
            catalogus = catalogus_mapping[iotype["catalogus"]]
            catalogus_label = _build_catalogus_label(catalogus)

            iotypen.append(
                {
                    "catalogus_domein": catalogus["domein"],
                    "catalogus_rsin": catalogus["rsin"],
                    "catalogus_label": catalogus_label,
                    "url": iotype["url"],
                    "omschrijving": iotype["omschrijving"],
                    # Not taken into account by the serializer, but used to filter duplicates:
                    "catalogus_url": iotype["catalogus"],
                }
            )

        return iotypen
