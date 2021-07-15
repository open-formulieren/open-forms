from typing import Optional

from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.registrations.base import BasePlugin
from openforms.registrations.constants import (
    REGISTRATION_ATTRIBUTE,
    RegistrationAttribute,
)
from openforms.registrations.registry import register
from openforms.submissions.mapping import (
    FieldConf,
    apply_data_mapping,
    get_unmapped_data,
)
from openforms.submissions.models import Submission, SubmissionReport

from .client import fmt_soap_date
from .models import StufZDSConfig


class ZaakOptionsSerializer(serializers.Serializer):
    zds_zaaktype_code = serializers.CharField(
        required=False,
        help_text=_("Zaaktype code for newly created Zaken in StUF-ZDS"),
    )
    zds_zaaktype_omschrijving = serializers.CharField(
        required=False,
        help_text=_("Zaaktype description for newly created Zaken in StUF-ZDS"),
    )


def json2soap_date(json_date):
    if not json_date:
        return None
    value = parse_date(json_date)
    return fmt_soap_date(value)


@register("stuf-zds-create-zaak")
class StufZDSRegistration(BasePlugin):
    verbose_name = _("StUF-ZDS")
    configuration_options = ZaakOptionsSerializer

    zaak_mapping = {
        "initiator.voornamen": RegistrationAttribute.initiator_voornamen,
        "initiator.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "initiator.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "initiator.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum, transform=json2soap_date
        ),
        # "initiator.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        "initiator.bsn": FieldConf(submission_field="bsn"),
        "initiator.kvk": FieldConf(submission_field="kvk"),
    }

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        config = StufZDSConfig.get_solo()
        config.apply_defaults_to(options)

        options["omschrijving"] = submission.form.name
        options["referentienummer"] = str(submission.uuid)

        client = config.get_client(options)

        zaak_id = client.create_zaak_identificatie()

        zaak_data = apply_data_mapping(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )
        extra_data = get_unmapped_data(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )

        client.create_zaak(zaak_id, zaak_data, extra_data)

        doc_id = client.create_document_identificatie()

        submission_report = SubmissionReport.objects.get(submission=submission)
        client.create_zaak_document(zaak_id, doc_id, submission_report)

        result = {
            "zaak": zaak_id,
            "document": doc_id,
        }
        return result
