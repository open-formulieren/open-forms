from typing import Dict, List, Optional, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from ...base import BasePlugin
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...registry import register
from .checks import check_config
from .models import ZgwConfig
from .service import (
    create_attachment_document,
    create_report_document,
    create_rol,
    create_status,
    create_zaak,
    relate_document,
    set_zaak_payment,
)


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
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


def _point_coordinate(value):
    if not value or not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"type": "Point", "coordinates": [value[0], value[1]]}


@register("zgw-create-zaak")
class ZGWRegistration(BasePlugin):
    verbose_name = _("ZGW API's")
    configuration_options = ZaakOptionsSerializer

    rol_mapping = {
        "betrokkeneIdentificatie.voornamen": RegistrationAttribute.initiator_voornamen,
        "betrokkeneIdentificatie.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "betrokkeneIdentificatie.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "betrokkeneIdentificatie.geboortedatum": RegistrationAttribute.initiator_geboortedatum,
        # "betrokkeneIdentificatie.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        "betrokkeneIdentificatie.inpBsn": FieldConf(submission_field="bsn"),
    }
    zaak_mapping = {
        "zaakgeometrie": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
    }

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        """
        Create a zaak and document with the submitted data as PDF.

        NOTE: this requires that the report was generated before the submission is
        being registered. See
        :meth:`openforms.submissions.api.viewsets.SubmissionViewSet._complete` where
        celery tasks are chained to guarantee this.
        """
        if not self.is_enabled:
            raise PluginNotEnabled()

        zgw = ZgwConfig.get_solo()
        zgw.apply_defaults_to(options)

        zaak_data = apply_data_mapping(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )
        zaak = create_zaak(
            options,
            payment_required=submission.payment_required,
            existing_reference=submission.public_registration_reference,
            **zaak_data
        )

        submission_report = SubmissionReport.objects.get(submission=submission)
        document = create_report_document(
            submission.form.admin_name, submission_report, options
        )
        relate_document(zaak["url"], document["url"])

        rol_data = apply_data_mapping(
            submission, self.rol_mapping, REGISTRATION_ATTRIBUTE
        )
        rol = create_rol(zaak, rol_data, options)

        # for now create generic status
        status = create_status(zaak)

        for attachment in submission.attachments:
            attachment = create_attachment_document(
                submission.form.admin_name, attachment, options
            )
            relate_document(zaak["url"], attachment["url"])

        result = {
            "zaak": zaak,
            "document": document,
            "status": status,
            "rol": rol,
        }
        return result

    def get_reference_from_result(self, result: Dict[str, str]) -> str:
        """
        Extract the public submission reference from the result data.

        This method must return a string to be saved on the submission model.

        :arg result: the raw underlying JSONField datastructure.

        .. warning::

            Technically the combination of (bronorganisatie,identicatie) must be unique,
            so if the same identification is generated by different Zaken APIs,
            this may cause problems!
        """
        # See response of
        # https://raw.githubusercontent.com/vng-Realisatie/zaken-api/1.0.0/src/openapi.yaml#operation/zaak_create
        zaak = result["zaak"]
        return zaak["identificatie"]

    def update_payment_status(self, submission: "Submission", options: dict):
        set_zaak_payment(submission.registration_result["zaak"]["url"])

    def check_config(self):
        check_config()

    def get_config_actions(self) -> List[Tuple[str, str]]:
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:zgw_apis_zgwconfig_change",
                    args=(ZgwConfig.singleton_instance_id,),
                ),
            ),
        ]
