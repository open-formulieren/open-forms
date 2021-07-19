import re
from dataclasses import dataclass
from typing import Optional

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


@dataclass
class PartialDate:
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None

    @property
    def indicator(self):
        if self.year and self.month and self.day:
            return "V"
        elif self.year and self.month:
            return "D"
        elif self.year:
            return "M"
        else:
            return "J"

    @property
    def value(self):
        if self.year and self.month and self.day:
            return f"{self.year:04}{self.month:02}{self.day:02}"
        elif self.year and self.month:
            return f"{self.year:04}{self.month:02}"
        elif self.year:
            return f"{self.year:04}"
        else:
            return ""

    def __str__(self):
        return self.value

    @classmethod
    def parse(cls, json_partial_date):
        if not json_partial_date:
            return cls()
        """
        2000-01-01
        2000-1-1
        2000-01
        2000-1
        2000
        """

        def _safe_int(num):
            try:
                return int(num)
            except TypeError:
                return None

        m = re.match(r"^(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?$", json_partial_date)
        if not m:
            return cls()
        else:
            return cls(
                _safe_int(m.group(1)), _safe_int(m.group(2)), _safe_int(m.group(3))
            )


@register("stuf-zds-create-zaak")
class StufZDSRegistration(BasePlugin):
    verbose_name = _("StUF-ZDS")
    configuration_options = ZaakOptionsSerializer

    zaak_mapping = {
        "initiator.voornamen": RegistrationAttribute.initiator_voornamen,
        "initiator.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "initiator.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "initiator.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum, transform=PartialDate.parse
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
