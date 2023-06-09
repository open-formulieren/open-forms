from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zds_client import Client
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType
from zgw_consumers.service import get_paginated_results

from openforms.api.views import ListMixin
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig, ZgwConfig

from .filters import ZgwApiGroupFilterSerializer
from .serializers import InformatieObjectTypeChoiceSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("List available InformatieObjectTypen"),
        parameters=[ZgwApiGroupFilterSerializer],
    ),
)
class InformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeChoiceSerializer

    def _get_ztc_client(self, zgw_api_group: ZGWApiGroupConfig | None) -> Client | None:
        if zgw_api_group:
            return zgw_api_group.ztc_service.build_client()

        config = ZgwConfig.get_solo()
        if config.default_zgw_api_group:
            return config.default_zgw_api_group.ztc_service.build_client()

    def get_objects(self):
        filter_serializer = ZgwApiGroupFilterSerializer(data=self.request.query_params)
        if not filter_serializer.is_valid():
            return []

        zgw_api_group = filter_serializer.validated_data.get("zgw_api_group")

        client = self._get_ztc_client(zgw_api_group)
        if not client:
            return []

        catalogus_data = get_paginated_results(client, "catalogus")
        catalogus_mapping = {
            catalogus["url"]: catalogus for catalogus in catalogus_data
        }

        iotypen_data = get_paginated_results(client, "informatieobjecttype")
        iotypen = [
            {
                "informatieobjecttype": factory(InformatieObjectType, iotype),
                "catalogus": factory(Catalogus, catalogus_mapping[iotype["catalogus"]]),
            }
            for iotype in iotypen_data
        ]

        return iotypen
