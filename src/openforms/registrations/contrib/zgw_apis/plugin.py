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
from openforms.submissions.models import Submission, SubmissionReport
from openforms.utils.validators import validate_rsin


class ZaakOptionsSerializer(serializers.Serializer):
    zaaktype = serializers.URLField(
        required=False, help_text=_("URL of the ZAAKTYPE in the Catalogi API")
    )
    informatieobjecttype = serializers.URLField(
        required=False,
        help_text=_("URL of the INFORMATIEOBJECTTYPE in the Catalogi API"),
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
            "Indication of the level to which extend the dossier of the ZAAK is meant to be public."
        ),
    )


@register(
    "zgw-create-zaak",
    _("ZGW API's"),
    configuration_options=ZaakOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_zaak_plugin(submission: Submission, options: dict) -> Optional[dict]:
    """
    Create a zaak and document with the submitted data as PDF.

    NOTE: this requires that the report was generated before the submission is
    being registered. See
    :meth:`openforms.submissions.api.viewsets.SubmissionViewSet._complete` where
    celery tasks are chained to guarantee this.
    """
    data = submission.get_merged_data()

    zgw = ZgwConfig.get_solo()
    zgw.apply_defaults_to(options)

    zaak = create_zaak(options)

    submission_report = SubmissionReport.objects.get(submission=submission)
    document = create_document(submission.form.name, submission_report, options)
    relate_document(zaak["url"], document["url"])

    # for now grab fixed data value
    initiator = {
        "betrokkeneIdentificatie": {
            """
            NOTE for the demo we pulled from some predefined fields,
                this would break with custom forms so if we want to set fields in the API we need some mapping solution

            additionally we need to define where to pull the inpBsn/anpIdentificatie/inpA_nummer
                the BSN is an authentication field but the others?

            (see also the stuf_zds registration plugin for more notes)
            """
            # simple for demo
            # "voornamen": data.get("voornaam", ""),
            # "geslachtsnaam": data.get("achternaam", ""),
            # "voorvoegselGeslachtsnaam": data.get("tussenvoegsel", ""),
            # "inpBsn": data.get("bsn", ""),
            # actual
            "inpBsn": submission.bsn,
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
