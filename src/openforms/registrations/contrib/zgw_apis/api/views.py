from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType
from zgw_consumers.service import get_paginated_results

from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.utils.api.views import ListMixin

from .serializers import InformatieObjectTypeChoiceSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available InformatieObjectTypen")),
)
class InformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeChoiceSerializer

    def get_objects(self):
        config = ZgwConfig().get_solo()

        if not config.ztc_service:
            return []

        client = config.ztc_service.build_client()

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
