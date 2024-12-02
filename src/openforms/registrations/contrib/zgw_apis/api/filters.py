from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.api.filters import (
    DocumentTypesFilter,
    ProvidesCatalogiClientQueryParamsSerializer,
)
from openforms.contrib.zgw.clients.catalogi import CatalogiClient

from ..client import get_catalogi_client
from ..models import ZGWApiGroupConfig


class ZGWAPIGroupMixin(serializers.Serializer):
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


class APIGroupQueryParamsSerializer(
    ZGWAPIGroupMixin, ProvidesCatalogiClientQueryParamsSerializer
):
    pass


class ListDocumentTypesQueryParamsSerializer(ZGWAPIGroupMixin, DocumentTypesFilter):
    pass


class ListCaseTypesQueryParamsSerializer(ZGWAPIGroupMixin, serializers.Serializer):
    catalogue_url = serializers.URLField(
        label=_("catalogus URL"),
        help_text=_("Filter case types against this catalogue URL."),
        required=True,
    )

    def get_fields(self):
        fields = super().get_fields()
        fields["zgw_api_group"].help_text = _(
            "The primary key of the ZGW API group to use. The case types from the "
            "Catalogi API in this group will be returned."
        )
        return fields


class FilterForCaseTypeQueryParamsSerializer(ZGWAPIGroupMixin, serializers.Serializer):
    catalogue_url = serializers.URLField(
        label=_("catalogus URL"),
        help_text=_("Filter case types against this catalogue URL."),
        required=True,
    )
    case_type_identification = serializers.CharField(
        label=_("case type identification"),
        help_text=_("Filter case types against this identification."),
        required=True,
    )
