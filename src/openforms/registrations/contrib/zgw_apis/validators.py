from functools import partial

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.contrib.zgw.service import match_omschrijving, retrieve_roltypen


class RoltypeOmschrijvingValidator:
    def __call__(self, data: dict):
        if not ("medewerker_roltype" in data and "zaaktype" in data):
            return

        roltype = retrieve_roltypen(
            matcher=partial(
                match_omschrijving, omschrijving=data["medewerker_roltype"]
            ),
            query_params={"zaaktype": data["zaaktype"]},
            ztc_service=data["zgw_api_group"].ztc_service,
        )

        if not roltype:
            raise serializers.ValidationError(
                detail=_(
                    "Could not find a roltype with this description related to the zaaktype"
                ),
                code="invalid",
            )
