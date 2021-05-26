from typing import Optional

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.registrations.contrib.stuf_zds.models import StufZDSConfig
from openforms.registrations.registry import register
from openforms.submissions.models import Submission


class ZaakOptionsSerializer(serializers.Serializer):
    zds_zaaktype_code = serializers.CharField(
        required=False,
        help_text=_("Zaaktype code for newly created Zaken in StUF-ZDS"),
    )
    zds_zaaktype_omschrijving = serializers.CharField(
        required=False,
        help_text=_("Zaaktype description for newly created Zaken in StUF-ZDS"),
    )


@register(
    "stuf-zds-create-zaak",
    _("StUF-ZDS"),
    configuration_options=ZaakOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_zaak_plugin(submission: Submission, options: dict) -> Optional[dict]:
    data = submission.get_merged_data()

    config = StufZDSConfig.get_solo()
    config.apply_defaults_to(options)

    options["omschrijving"] = submission.form.name
    options["referentienummer"] = str(submission.uuid)

    client = config.get_client()

    zaak_id = client.create_zaak_identificatie(options)
    client.create_zaak(options, zaak_id, data)
    # zaak_id = "0000c765c781-cedc-4c17-bc25-6a80ec24de07"

    doc_id = client.create_document_identificatie(options)
    client.create_zaak_document(options, zaak_id, doc_id, data)

    result = {
        "zaak": zaak_id,
        "document": doc_id,
    }
    return result
