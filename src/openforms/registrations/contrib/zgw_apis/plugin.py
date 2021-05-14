from typing import Optional

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.registrations.contrib.zgw_apis.service import (
    create_document,
    create_rol,
    create_status,
    create_zaak,
    relate_document,
)
from openforms.registrations.registry import register
from openforms.submissions.models import Submission
from openforms.utils.validators import validate_rsin


class ZaakOptionsSerializer(serializers.Serializer):
    zaaktype = serializers.URLField(
        required=False, help_text=_("URL of the ZAAKTYPE in Catalogi API")
    )
    informatieobjecttype = serializers.URLField(
        required=False, help_text=_("URL of the INFORMATIEOBJECTTYPE in Catalogi API")
    )
    organisatie_rsin = serializers.CharField(
        required=False,
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the ZAAK"),
    )
    vertrouwelijkheidaanduiding = serializers.ChoiceField(
        required=False,
        choices=VertrouwelijkheidsAanduidingen.choices,
        help_text=_(
            "Aanduiding van de mate waarin het zaakdossier van de ZAAK voor de openbaarheid bestemd is."
        ),
    )


@register(
    "zgw-create-zaak",
    "Registreer zaak met Zaakgericht werken API's",
    configuration_options=ZaakOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_zaak_plugin(submission: Submission, options: dict) -> Optional[dict]:
    data = submission.get_merged_data()

    zgw = ZgwConfig.get_solo()
    zgw.apply_defaults_to(options)

    zaak = create_zaak(options)
    document = create_document(submission.form.name, data, options)
    relate_document(zaak["url"], document["url"])

    # for now grab fixed data value
    initiator = {
        "betrokkeneIdentificatie": {
            # simple for demo
            "voornamen": data.get("voornaam", ""),
            "geslachtsnaam": data.get("achternaam", ""),
            "voorvoegselGeslachtsnaam": data.get("tussenvoegsel", ""),
            "inpBsn": data.get("bsn", ""),
            # actual
            # "inpBsn": data.get("inpBsn", ""),
            # "anpIdentificatie": data.get("anpIdentificatie", ""),
            # "inpA_nummer": data.get("inpA_nummer", ""),
            # "geslachtsnaam": data.get("geslachtsnaam", ""),
            # "voorvoegselGeslachtsnaam": data.get("voorvoegselGeslachtsnaam", ""),
            # "voorletters": data.get("voorletters", ""),
            # "voornamen": data.get("voornamen", ""),
            # "geslachtsaanduiding": data.get("geslachtsaanduiding", "o"),
            # "geboortedatum": data.get("geboortedatum", ""),
        },
        "roltoelichting": "inzender formulier",
    }
    rol = create_rol(zaak, initiator, options)

    # for now create generic status
    status = create_status(zaak)

    result = {
        "zaak": zaak,
        "document": document,
        "status": status,
        "rol": rol,
    }
    return result
