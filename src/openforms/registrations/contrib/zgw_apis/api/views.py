from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus, ZaakType

from openforms.api.views import ListMixin

from .filters import ListZaakTypenQueryParamsSerializer
from .serializers import ZaakTypeChoiceSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("List available ZaakTypen"),
        parameters=[ListZaakTypenQueryParamsSerializer],
    ),
)
class ZaakTypenListView(ListMixin, APIView):
    """
    List the available ZaakTypen based on the configured ZGW API set.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ZaakTypeChoiceSerializer

    def get_objects(self):
        filter_serializer = ListZaakTypenQueryParamsSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        client = filter_serializer.get_ztc_client()

        catalogus_data = client.get_all_catalogi()
        catalogus_mapping = {
            catalogus["url"]: catalogus for catalogus in catalogus_data
        }

        zaaktypen_data = client.get_all_zaaktypen()
        zaaktypen = [
            {
                "zaaktype": factory(ZaakType, zaaktype),
                "catalogus": factory(
                    Catalogus, catalogus_mapping[zaaktype["catalogus"]]
                ),
            }
            for zaaktype in zaaktypen_data
        ]

        return zaaktypen
