from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.contrib.zgw.service import retrieve_roltype


class RoltypeOmschrijvingValidator:
    def __call__(self, data: dict):
        if not ("medewerker_roltype" in data and "zaaktype" in data):
            return

        roltype = retrieve_roltype(
            data["medewerker_roltype"], **{"zaaktype": data["zaaktype"]}
        )

        if not roltype:
            raise serializers.ValidationError(
                detail=_(
                    "Could not find a roltype with this description related to the zaaktype"
                ),
                code="invalid",
            )
