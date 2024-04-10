import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.base import BasePlugin
from openforms.registrations.constants import (
    REGISTRATION_ATTRIBUTE,
    RegistrationAttribute,
)
from openforms.submissions.mapping import (
    SKIP,
    FieldConf,
    apply_data_mapping,
    get_component,
    get_unmapped_data,
)
from openforms.submissions.models import Submission, SubmissionReport
from openforms.utils.mixins import JsonSchemaSerializerMixin
from stuf.stuf_zds.client import PaymentStatus
from stuf.stuf_zds.constants import VertrouwelijkheidsAanduidingen
from stuf.stuf_zds.models import StufZDSConfig

from ...registry import register
from ...utils import execute_unless_result_exists
from .utils import flatten_data

logger = logging.getLogger(__name__)


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    gemeentecode = serializers.CharField(
        required=False,
        help_text=_("Municipality code to register zaken"),
    )

    zds_zaaktype_code = serializers.CharField(
        required=True,
        help_text=_("Zaaktype code for newly created Zaken in StUF-ZDS"),
    )
    zds_zaaktype_omschrijving = serializers.CharField(
        required=False,
        help_text=_("Zaaktype description for newly created Zaken in StUF-ZDS"),
    )

    zds_zaaktype_status_code = serializers.CharField(
        required=False,
        help_text=_("Zaaktype status code for newly created zaken in StUF-ZDS"),
    )
    zds_zaaktype_status_omschrijving = serializers.CharField(
        required=False,
        help_text=_("Zaaktype status omschrijving for newly created zaken in StUF-ZDS"),
    )

    zds_documenttype_omschrijving_inzending = serializers.CharField(
        required=True,
        help_text=_("Documenttype description for newly created zaken in StUF-ZDS"),
    )

    zds_zaakdoc_vertrouwelijkheid = serializers.ChoiceField(
        label=_("Document confidentiality level"),
        choices=VertrouwelijkheidsAanduidingen.choices,
        # older versions from before this version was added do not have this field in
        # the saved data. In those cases, the default is used.
        default=VertrouwelijkheidsAanduidingen.vertrouwelijk,
        help_text=_(
            "Indication of the level to which extend the dossier of the ZAAK is meant "
            "to be public. This is set on the documents created for the ZAAK."
        ),
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
                num = int(num)
                if num == 0:
                    return None
                else:
                    return num
            except TypeError:
                return None

        m = re.match(r"^(0|\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?$", json_partial_date)
        if not m:
            return cls()
        else:
            return cls(
                _safe_int(m.group(1)), _safe_int(m.group(2)), _safe_int(m.group(3))
            )


def _point_coordinate(value):
    if not value or not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"lat": value[0], "lng": value[1]}


def _gender_choices(value):
    """
    Convert value to uppercase, take only the first character and see if it's
    valid for StUF 'geslachtsaanduiding'.
    """
    value = str(value).upper()[:1]
    if value not in ["M", "V", "O"]:
        return SKIP
    return value


@register("stuf-zds-create-zaak")
class StufZDSRegistration(BasePlugin):
    verbose_name = _("StUF-ZDS")
    configuration_options = ZaakOptionsSerializer

    zaak_mapping = {
        # Initiator
        # Medewerker
        "initiator.medewerker_nummer": RegistrationAttribute.initiator_medewerker_nummer,
        # Natuurlijk Persoon
        "initiator.voorletters": RegistrationAttribute.initiator_voorletters,
        "initiator.voornamen": RegistrationAttribute.initiator_voornamen,
        "initiator.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "initiator.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "initiator.geslachtsaanduiding": FieldConf(
            RegistrationAttribute.initiator_geslachtsaanduiding,
            transform=_gender_choices,
        ),
        "initiator.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum, transform=PartialDate.parse
        ),
        # "initiator.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        # Verblijfsadres for both Natuurlijk Persoon and Vestiging
        "initiator.verblijfsadres.woonplaatsNaam": RegistrationAttribute.initiator_woonplaats,
        "initiator.verblijfsadres.postcode": RegistrationAttribute.initiator_postcode,
        "initiator.verblijfsadres.straatnaam": RegistrationAttribute.initiator_straat,
        "initiator.verblijfsadres.huisnummer": RegistrationAttribute.initiator_huisnummer,
        "initiator.verblijfsadres.huisletter": RegistrationAttribute.initiator_huisletter,
        "initiator.verblijfsadres.huisnummertoevoeging": RegistrationAttribute.initiator_huisnummer_toevoeging,
        # Vestiging
        "initiator.vestigingsNummer": RegistrationAttribute.initiator_vestigingsnummer,
        "initiator.handelsnaam": RegistrationAttribute.initiator_handelsnaam,
        # Identifiers
        "initiator.bsn": FieldConf(submission_auth_info_attribute="bsn"),
        "initiator.kvk": FieldConf(submission_auth_info_attribute="kvk"),
        # Location
        "locatie": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
    }

    def pre_register_submission(self, submission: "Submission", options: dict) -> None:
        config = StufZDSConfig.get_solo()
        config.apply_defaults_to(options)

        with config.get_client(options) as client:
            # obtain a zaaknummer & save it - first, check if we have an intermediate result
            # from earlier attempts. if we do, do not generate a new number
            zaak_id = execute_unless_result_exists(
                client.create_zaak_identificatie,
                submission,
                "intermediate.zaaknummer",
                default="",
            )

        submission.public_registration_reference = zaak_id
        submission.save()

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        """
        Register the submission by creating a ZAAK.

        Any attachments and the submission report are added as ZAAK-DOCUMENTs.

        Because of the various calls needed to come to the "end-result", we store the
        intermediate results on the submission in the event retries are needed. This
        prevents Open Forms from reserving case numbers over and over again (for
        example). See #1183 for a reported issue about this.
        """
        config = StufZDSConfig.get_solo()
        config.apply_defaults_to(options)

        options["omschrijving"] = submission.form.admin_name

        with config.get_client(options) as client:
            # Zaak ID reserved during the pre-registration phase
            zaak_id = submission.public_registration_reference

            zaak_data = apply_data_mapping(
                submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
            )
            if zaak_data.get("locatie"):
                zaak_data["locatie"]["key"] = get_component(
                    submission,
                    RegistrationAttribute.locatie_coordinaat,
                    REGISTRATION_ATTRIBUTE,
                )["key"]

            extra_data = get_unmapped_data(
                submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
            )
            # The extraElement tag of StUF-ZDS expects primitive types
            extra_data = flatten_data(extra_data)

            if internal_reference := submission.registration_result.get(
                "temporary_internal_reference",
            ):
                zaak_data.update({"kenmerken": [internal_reference]})

            # Add medewerker to the data
            if submission.has_registrator:
                zaak_data.update(
                    {
                        "registrator": {
                            "medewerker": {
                                "identificatie": submission.registrator.value
                            }
                        }
                    }
                )

            class LangInjection:
                """Ensures the first extra element is the submission language
                and isn't shadowed by a form field with the same key"""

                def items(self):
                    yield ("language_code", submission.language_code)
                    yield from extra_data.items()

            payment_status = (
                PaymentStatus.NVT
                if not submission.payment_required
                else (
                    PaymentStatus.FULL
                    if submission.payment_user_has_paid
                    else PaymentStatus.NOT_YET
                )
            )
            zaak_data.update({"betalings_indicatie": payment_status})

            execute_unless_result_exists(
                lambda: client.create_zaak(zaak_id, zaak_data, LangInjection()),
                submission,
                "intermediate.zaak_created",
                default=False,
                result=True,
            )

            doc_id = execute_unless_result_exists(
                client.create_document_identificatie,
                submission,
                "intermediate.document_nummers.pdf-report",
                default="",
            )
            submission_report = SubmissionReport.objects.get(submission=submission)
            execute_unless_result_exists(
                lambda: client.create_zaak_document(zaak_id, doc_id, submission_report),
                submission,
                "intermediate.documents_created.pdf-report",
                default=False,
                result=True,
            )

            for attachment in submission.attachments:
                attachment_doc_id = execute_unless_result_exists(
                    client.create_document_identificatie,
                    submission,
                    f"intermediate.document_nummers.{attachment.id}",
                    default="",
                )
                execute_unless_result_exists(
                    lambda: client.create_zaak_attachment(
                        zaak_id, attachment_doc_id, attachment
                    ),
                    submission,
                    f"intermediate.documents_created.{attachment.id}",
                    default=False,
                    result=True,
                )

        result = {
            "zaak": zaak_id,
            "document": doc_id,
        }
        return result

    def get_reference_from_result(self, result: Dict[str, str]) -> str:
        """
        Extract the public submission reference from the result data.

        This method must return a string to be saved on the submission model.

        :arg result: the raw underlying JSONField datastructure.

        .. warning::

            Technically the combination of (bronorganisatie,identicatie) must be unique,
            so if the same identification is generated by different Zaaksystemen,
            this may cause problems!
        """
        return result["zaak"]

    def update_payment_status(self, submission: "Submission", options: dict):
        config = StufZDSConfig.get_solo()
        config.apply_defaults_to(options)
        with config.get_client(options) as client:
            client.set_zaak_payment(
                submission.registration_result["zaak"],
            )

    def check_config(self):
        config = StufZDSConfig.get_solo()
        if not config.service_id:
            raise InvalidPluginConfiguration(_("StufService not selected"))
        if not config.gemeentecode:
            raise InvalidPluginConfiguration(
                _("StufService missing setting '{name}'").format(name="gemeentecode")
            )

        options = {
            "omschrijving": "MyForm",
            "zds_zaaktype_code": "test",
            "zds_zaaktype_omschrijving": "test",
            "zds_zaaktype_status_code": "test",
            "zds_zaaktype_status_omschrijving": "test",
            "zds_documenttype_omschrijving_inzending": "test",
        }
        config.apply_defaults_to(options)
        with config.get_client(options) as client:
            try:
                client.check_config()
            except Exception as e:
                raise InvalidPluginConfiguration(
                    _("Could not connect: {exception}").format(exception=e)
                ) from e

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:stuf_zds_stufzdsconfig_change",
                    args=(StufZDSConfig.singleton_instance_id,),
                ),
            ),
        ]
