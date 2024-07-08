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

    Each ZaakType is uniquely identified by its 'omschrijving', 'catalogus',
    and beginning and end date. If multiple same ZaakTypen exist for different dates,
    only one entry is returned.
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
        zaaktypen = []

        for zaaktype in zaaktypen_data:
            exists = any(
                existing_zaaktype["zaaktype"].omschrijving == zaaktype["omschrijving"]
                and existing_zaaktype["zaaktype"].catalogus == zaaktype["catalogus"]
                for existing_zaaktype in zaaktypen
            )

            if not exists:
                zaaktypen.append(
                    {
                        "zaaktype": factory(ZaakType, zaaktype),
                        "catalogus": factory(
                            Catalogus, catalogus_mapping[zaaktype["catalogus"]]
                        ),
                    }
                )

        return zaaktypen
