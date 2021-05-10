from typing import Optional

from rest_framework import serializers

from openforms.registrations.contrib.stuf_zds.client import StufZDSClient
from openforms.registrations.contrib.stuf_zds.models import StufZDSConfig
from openforms.registrations.registry import register
from openforms.submissions.models import Submission


class ZaakOptionsSerializer(serializers.Serializer):
    pass


@register(
    "stuf-zds-create-zaak",
    "Create StUF-ZDS Zaak",
    configuration_options=ZaakOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_zaak_plugin(submission: Submission, options: dict) -> Optional[dict]:
    data = {}
    for step in submission.steps:
        data.update(step.data)

    config = StufZDSConfig.get_solo()
    config.apply_defaults_to(options)

    options["omschrijving"] = submission.form.name

    client = config.service.build_client()

    zaak_id = client.create_zaak_identificatie()
    client.create_zaak(options, zaak_id)

    doc_id = client.create_document_identificatie()
    client.create_zaak_document(options, zaak_id, doc_id, data)

    result = {
        "zaak": zaak_id,
        "document": doc_id,
    }
    return result
