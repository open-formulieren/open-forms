from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.client import build_client

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.api.filters import (
    DocumentTypesFilter,
    ProvidesCatalogiClientQueryParamsSerializer,
)
from openforms.contrib.zgw.clients.catalogi import CatalogiClient

from ..models import ObjectsAPIGroupConfig


class ObjectsAPIGroupMixin(serializers.Serializer):
    objects_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(catalogi_service=None),
        help_text=_(
            "The primary key of the Objects API group to use. The informatieobjecttypen from the Catalogi API "
            "in this group will be returned."
        ),
        label=_("Objects API group"),
    )

    def get_ztc_client(self) -> CatalogiClient:
        objects_api_group: ObjectsAPIGroupConfig = self.validated_data[
            "objects_api_group"
        ]
        return build_client(
            objects_api_group.catalogi_service, client_factory=CatalogiClient
        )


class APIGroupQueryParamsSerializer(
    ObjectsAPIGroupMixin, ProvidesCatalogiClientQueryParamsSerializer
):
    pass


class ListDocumentTypesQueryParamsSerializer(ObjectsAPIGroupMixin, DocumentTypesFilter):
    pass
