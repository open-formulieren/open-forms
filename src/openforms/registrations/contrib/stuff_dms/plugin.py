from typing import Optional

from rest_framework import serializers

from openforms.registrations.contrib.stuff_dms.models import StufDMSConfig
from openforms.registrations.contrib.stuff_dms.services import (
    add_zaak_document,
    create_document_identificatie,
    create_zaak,
    create_zaak_identificatie,
)
from openforms.registrations.registry import register
from openforms.submissions.models import Submission


class ZaakOptionsSerializer(serializers.Serializer):
    pass


@register(
    "stuf-dms-create-zaak",
    "Create StUF-DMS Zaak",
    configuration_options=ZaakOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_zaak_plugin(submission: Submission, options: dict) -> Optional[dict]:
    data = {}
    for step in submission.steps:
        data.update(step.data)

    config = StufDMSConfig.get_solo()
    config.apply_defaults_to(options)

    zaak_id = create_zaak_identificatie(config, options, data)
    zaak = create_zaak(config, options, data, zaak_id)
    doc_id = create_document_identificatie(config, options, data)
    doc_id = add_zaak_document(config, options, zaak_id, doc_id)

    result = {
        "zaak": "TODO",
        "document": "TODO",
    }
    return result
