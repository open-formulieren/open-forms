from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.client import build_client

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.clients.catalogi import CatalogiClient
from openforms.registrations.contrib.objects_api.models import (
    ObjectsAPIConfig,
    ObjectsAPIGroupConfig,
)
from openforms.registrations.contrib.zgw_apis.client import get_catalogi_client
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig, ZgwConfig

from ..registry import register


class ListInformatieObjectTypenQueryParamsSerializer(serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.all(),
        help_text=_(
            "The primary key of the ZGW API set to use. If provided, the informatieobjecttypen from the Catalogi API "
            "in this set will be returned. Otherwise, the Catalogi API in the default ZGW API set will be used to find "
            "informatieobjecttypen."
        ),
        label=_("ZGW API set"),
        required=False,
    )
    objects_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.all(),
        help_text=_(
            "The primary key of the Objects API group to use. If provided, the informatieobjecttypen from the Catalogi API "
            "in this group will be returned. Otherwise, the Catalogi API in the default Objects API group will be used to find "
            "informatieobjecttypen."
        ),
        label=_("Objects API group"),
        required=False,
    )
    registration_backend = serializers.ChoiceField(
        help_text=_("The ID of the registration backend to use."),
        label=_("Registration backend ID"),
        choices=[],
    )

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        fields["registration_backend"].choices = register.get_choices()
        return fields

    def get_ztc_client(self) -> CatalogiClient | None:
        registration_backend = self.validated_data.get("registration_backend")
        zgw_api_group: ZGWApiGroupConfig | None = self.validated_data.get(
            "zgw_api_group"
        )
        objects_api_group: ObjectsAPIGroupConfig | None = self.validated_data.get(
            "objects_api_group"
        )

        if registration_backend == "zgw-create-zaak":
            if zgw_api_group is not None:
                return get_catalogi_client(zgw_api_group)
            else:
                config = ZgwConfig.get_solo()
                assert isinstance(config, ZgwConfig)
                if group := config.default_zgw_api_group:
                    return get_catalogi_client(group)
        elif registration_backend == "objects_api":
            if objects_api_group is not None:
                service = objects_api_group.catalogi_service
            else:
                config = ObjectsAPIConfig.get_solo()
                assert isinstance(config, ObjectsAPIConfig)
                if config.default_objects_api_group is None:
                    return
                service = config.default_objects_api_group.catalogi_service

            if service is not None:
                return build_client(service, client_factory=CatalogiClient)
