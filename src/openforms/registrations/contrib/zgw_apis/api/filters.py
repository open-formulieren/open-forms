from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.clients.catalogi import CatalogiClient
from openforms.registrations.contrib.zgw_apis.client import get_catalogi_client
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig


class ListZaakTypenQueryParamsSerializer(serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.all(),
        help_text=_(
            "The primary key of the ZGW API set to use. The zaaktypen from the Catalogi API "
            "in this set will be returned."
        ),
        label=_("ZGW API set"),
    )

    def get_ztc_client(self) -> CatalogiClient:
        zgw_api_group: ZGWApiGroupConfig = self.validated_data["zgw_api_group"]
        return get_catalogi_client(zgw_api_group)
