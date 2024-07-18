from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.api.filters import (
    ProvidesCatalogiClientQueryParamsSerializer,
)
from openforms.contrib.zgw.clients.catalogi import CatalogiClient

from ..client import get_catalogi_client
from ..models import ZGWApiGroupConfig


class APIGroupQueryParamsSerializer(ProvidesCatalogiClientQueryParamsSerializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.exclude(drc_service=None),
        help_text=_(
            "The primary key of the ZGW API group to use. The informatieobjecttypen from the Catalogi API "
            "in this group will be returned."
        ),
        label=_("ZGW API group"),
    )

    def get_ztc_client(self) -> CatalogiClient:
        zgw_api_group: ZGWApiGroupConfig = self.validated_data["zgw_api_group"]
        return get_catalogi_client(zgw_api_group)


class ListInformatieObjectTypenQueryParamsSerializer(APIGroupQueryParamsSerializer):
    catalogus_url = serializers.URLField(
        label=_("catalogus URL"),
        help_text=_("Filter informatieobjecttypen against this catalogus URL."),
        required=False,
    )
