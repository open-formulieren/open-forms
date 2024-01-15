from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.clients.catalogi import CatalogiClient
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.registrations.contrib.zgw_apis.client import get_catalogi_client
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig, ZgwConfig
from zgw_consumers_ext.api_client import build_client

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
    registration_backend = serializers.ChoiceField(
        help_text=_("The ID of the registration backend to use."),
        label=_("Registration backend ID"),
        required=False,
        choices=[],
    )

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        if "registration_backend" in fields:
            fields["registration_backend"].choices = register.get_choices()
        return fields

    def get_ztc_client(self) -> CatalogiClient | None:
        registration_backend = self.validated_data.get("registration_backend")
        zgw_api_group: ZGWApiGroupConfig = self.validated_data.get("zgw_api_group")

        if registration_backend == "zgw-create-zaak" and zgw_api_group is not None:
            return get_catalogi_client(zgw_api_group)
        elif registration_backend == "objects_api":
            config = ObjectsAPIConfig.get_solo()
            if service := config.catalogi_service:
                return build_client(service, client_factory=CatalogiClient)

        config = ZgwConfig.get_solo()
        if group := config.default_zgw_api_group:
            return get_catalogi_client(group)
