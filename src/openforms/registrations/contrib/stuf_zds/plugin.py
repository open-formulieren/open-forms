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
from openforms.registrations.registry import register
from openforms.submissions.mapping import (
    SKIP,
    FieldConf,
    apply_data_mapping,
    get_component,
    get_unmapped_data,
)
from openforms.submissions.models import Submission, SubmissionReport
from openforms.utils.mixins import JsonSchemaSerializerMixin
from stuf.stuf_zds.models import StufZDSConfig


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
        required=True,
        help_text=_("Zaaktype description for newly created Zaken in StUF-ZDS"),
    )

    zds_zaaktype_status_code = serializers.CharField(
        required=True,
        help_text=_("Zaaktype status code for newly created zaken in StUF-ZDS"),
    )
    zds_zaaktype_status_omschrijving = serializers.CharField(
        required=True,
        help_text=_("Zaaktype status omschrijving for newly created zaken in StUF-ZDS"),
    )

    zds_documenttype_omschrijving_inzending = serializers.CharField(
        required=True,
        help_text=_("Documenttype description for newly created zaken in StUF-ZDS"),
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


@register("stuf-zds-create-zaak")
class StufZDSRegistration(BasePlugin):
    verbose_name = _("StUF-ZDS")
    configuration_options = ZaakOptionsSerializer

    zaak_mapping = {
        "initiator.voornamen": RegistrationAttribute.initiator_voornamen,
        "initiator.voorletters": RegistrationAttribute.initiator_voorletters,
        "initiator.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "initiator.tussenvoegsel": RegistrationAttribute.initiator_tussenvoegsel,
        "initiator.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum, transform=PartialDate.parse
        ),
        "initiator.adres.straat": RegistrationAttribute.initiator_straat,
        "initiator.adres.huisnummer": RegistrationAttribute.initiator_huisnummer,
        "initiator.adres.huisletter": RegistrationAttribute.initiator_huisletter,
        "initiator.adres.huisnummer_toevoeging": RegistrationAttribute.initiator_huisnummer_toevoeging,
        "initiator.adres.postcode": RegistrationAttribute.initiator_postcode,
        "initiator.adres.plaats": RegistrationAttribute.initiator_woonplaats,
        "initiator.telefoonnummer": RegistrationAttribute.initiator_telefoonnummer,
        "initiator.mailadres": RegistrationAttribute.initiator_mailadres,
        # "initiator.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        "initiator.handelsnaam": RegistrationAttribute.initiator_handelsnaam,
        # "initiator.kvk_nummer": RegistrationAttribute.initiator_kvk_nummer
        "initiator.vestigingsnummer": RegistrationAttribute.initiator_vestigingsnummer,
        "initiator.bsn": FieldConf(submission_field="bsn"),
        "initiator.kvk": FieldConf(submission_field="kvk"),
        # "locatie": FieldConf(
        #     RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        # ),
        "locatie.coordinaat": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
        "locatie.straat": RegistrationAttribute.locatie_straat,
        "locatie.huisnummer": RegistrationAttribute.locatie_huisnummer,
        "locatie.huisletter": RegistrationAttribute.locatie_huisletter,
        "locatie.huisnummer_toevoeging": RegistrationAttribute.locatie_huisnummer_toevoeging,
        "locatie.postcode": RegistrationAttribute.locatie_postcode,
        "locatie.plaats": RegistrationAttribute.locatie_stad,
        # roles
        # derdepartij
        "derdepartij.voornamen": RegistrationAttribute.derdepartij_voornamen,
        "derdepartij.voorletters": RegistrationAttribute.derdepartij_voorletters,
        "derdepartij.tussenvoegsel": RegistrationAttribute.derdepartij_tussenvoegsel,
        "derdepartij.geslachtsnaam": RegistrationAttribute.derdepartij_geslachtsnaam,
        "derdepartij.straat": RegistrationAttribute.derdepartij_straat,
        "derdepartij.huisnummer": RegistrationAttribute.derdepartij_huisnummer,
        "derdepartij.huisletter": RegistrationAttribute.derdepartij_huisletter,
        "derdepartij.huisnummer_toevoeging": RegistrationAttribute.derdepartij_huisnummer_toevoeging,
        "derdepartij.postcode": RegistrationAttribute.derdepartij_postcode,
        "derdepartij.plaats": RegistrationAttribute.derdepartij_stad,
        "derdepartij.telefoonnummer": RegistrationAttribute.derdepartij_telefoonnummer,
        "derdepartij.mailadres": RegistrationAttribute.derdepartij_mailadres,
        # contactpersoon
        "contact.voornamen": RegistrationAttribute.contact_voornamen,
        "contact.voorletters": RegistrationAttribute.contact_voorletters,
        "contact.tussenvoegsel": RegistrationAttribute.contact_tussenvoegsel,
        "contact.geslachtsnaam": RegistrationAttribute.contact_geslachtsnaam,
        "contact.straat": RegistrationAttribute.contact_straat,
        "contact.huisnummer": RegistrationAttribute.contact_huisnummer,
        "contact.huisletter": RegistrationAttribute.contact_huisletter,
        "contact.huisnummer_toevoeging": RegistrationAttribute.contact_huisnummer_toevoeging,
        "contact.postcode": RegistrationAttribute.contact_postcode,
        "contact.plaats": RegistrationAttribute.contact_stad,
        "contact.telefoonnummer": RegistrationAttribute.contact_telefoonnummer,
        "contact.mailadres": RegistrationAttribute.contact_mailadres,
        # gemachtigde
        "gemachtigde.voornamen": RegistrationAttribute.gemachtigde_voornamen,
        "gemachtigde.voorletters": RegistrationAttribute.gemachtigde_voorletters,
        "gemachtigde.tussenvoegsel": RegistrationAttribute.gemachtigde_tussenvoegsel,
        "gemachtigde.geslachtsnaam": RegistrationAttribute.gemachtigde_geslachtsnaam,
        "gemachtigde.straat": RegistrationAttribute.gemachtigde_straat,
        "gemachtigde.huisnummer": RegistrationAttribute.gemachtigde_huisnummer,
        "gemachtigde.huisletter": RegistrationAttribute.gemachtigde_huisletter,
        "gemachtigde.huisnummer_toevoeging": RegistrationAttribute.gemachtigde_huisnummer_toevoeging,
        "gemachtigde.postcode": RegistrationAttribute.gemachtigde_postcode,
        "gemachtigde.plaats": RegistrationAttribute.gemachtigde_stad,
        "gemachtigde.telefoonnummer": RegistrationAttribute.gemachtigde_telefoonnummer,
        "gemachtigde.mailadres": RegistrationAttribute.gemachtigde_mailadres,
        # overige rollen
        "overige.voornamen": RegistrationAttribute.overige_voornamen,
        "overige.voorletters": RegistrationAttribute.overige_voorletters,
        "overige.tussenvoegsel": RegistrationAttribute.overige_tussenvoegsel,
        "overige.geslachtsnaam": RegistrationAttribute.overige_geslachtsnaam,
        "overige.straat": RegistrationAttribute.overige_straat,
        "overige.huisnummer": RegistrationAttribute.overige_huisnummer,
        "overige.huisletter": RegistrationAttribute.overige_huisletter,
        "overige.huisnummer_toevoeging": RegistrationAttribute.overige_huisnummer_toevoeging,
        "overige.postcode": RegistrationAttribute.overige_postcode,
        "overige.plaats": RegistrationAttribute.overige_stad,
        "overige.telefoonnummer": RegistrationAttribute.overige_telefoonnummer,
        "overige.mailadres": RegistrationAttribute.overige_mailadres,
    }

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        config = StufZDSConfig.get_solo()
        config.apply_defaults_to(options)

        options["omschrijving"] = submission.form.admin_name
        options["referentienummer"] = str(submission.uuid)

        client = config.get_client(options)

        zaak_id = client.create_zaak_identificatie()

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

        if submission.public_registration_reference:
            zaak_data.update({"kenmerken": [submission.public_registration_reference]})

        client.create_zaak(zaak_id, zaak_data, extra_data, submission.payment_required)

        doc_id = client.create_document_identificatie()

        submission_report = SubmissionReport.objects.get(submission=submission)
        client.create_zaak_document(zaak_id, doc_id, submission_report)

        for attachment in submission.attachments:
            attachment_doc_id = client.create_document_identificatie()
            client.create_zaak_attachment(zaak_id, attachment_doc_id, attachment)

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
        client = config.get_client(options)
        client.set_zaak_payment(submission.registration_result["zaak"])

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
            "referentienummer": "123",
            "zds_zaaktype_code": "test",
            "zds_zaaktype_omschrijving": "test",
            "zds_zaaktype_status_code": "test",
            "zds_zaaktype_status_omschrijving": "test",
            "zds_documenttype_omschrijving_inzending": "test",
        }
        config.apply_defaults_to(options)
        client = config.get_client(options)
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
