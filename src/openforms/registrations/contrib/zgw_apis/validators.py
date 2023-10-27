from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.contrib.zgw.clients.catalogi import omschrijving_matcher

from .client import get_catalogi_client
from .models import ZgwConfig


class ValidateDefaultZgwApiGroup:
    def __call__(self, data: dict):
        if data.get("zgw_api_group") is None:
            config = ZgwConfig.get_solo()
            if config.default_zgw_api_group is None:
                raise ValidationError(
                    {
                        "zgw_api_group": _(
                            "No ZGW API set was configured on the form and no default was specified globally."
                        )
                    }
                )

        return data


class RoltypeOmschrijvingValidator:
    def __call__(self, data: dict):
        if not ("medewerker_roltype" in data and "zaaktype" in data):
            return

        from .plugin import ZGWRegistration

        group_config = ZGWRegistration.get_zgw_config(data)

        with get_catalogi_client(group_config) as client:
            roltypen = client.list_roltypen(
                zaaktype=data["zaaktype"],
                matcher=omschrijving_matcher(data["medewerker_roltype"]),
            )

        if not roltypen:
            raise serializers.ValidationError(
                detail=_(
                    "Could not find a roltype with this description related to the zaaktype"
                ),
                code="invalid",
            )
