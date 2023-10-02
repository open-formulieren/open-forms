from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.contrib.zgw.clients.catalogi import omschrijving_matcher

from .client import get_catalogi_client


class RoltypeOmschrijvingValidator:
    def __call__(self, data: dict):
        if not ("medewerker_roltype" in data and "zaaktype" in data):
            return

        with get_catalogi_client(data["zgw_api_group"]) as client:
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
