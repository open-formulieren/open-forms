from functools import partial, wraps
from typing import Dict, List, Optional, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
from rest_framework import serializers
from zds_client import ClientError
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_report_document,
    create_rol,
    create_status,
    create_zaak,
    relate_document,
    set_zaak_payment,
)
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from ...base import BasePlugin
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...exceptions import RegistrationFailed
from ...registry import register
from ...utils import execute_unless_result_exists
from .checks import check_config
from .models import ZgwConfig


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


def _gender_choices(value):
    """
    Convert value to lowercase, take only the first character and see if it's
    valid for ZGW APIs 'geslachtsaanduiding'.
    """
    value = str(value).lower()[:1]
    if value not in ["m", "v", "o"]:
        return SKIP
    return value


def wrap_api_errors(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (requests.RequestException, ClientError) as exc:
            raise RegistrationFailed from exc

    return decorator


@register("zgw-create-zaak")
class ZGWRegistration(BasePlugin):
    verbose_name = _("ZGW API's")
    configuration_options = ZaakOptionsSerializer

    rol_mapping = {
        # Initiator
        # Natuurlijk Persoon
        "betrokkeneIdentificatie.voorletters": RegistrationAttribute.initiator_voorletters,
        "betrokkeneIdentificatie.voornamen": RegistrationAttribute.initiator_voornamen,
        "betrokkeneIdentificatie.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "betrokkeneIdentificatie.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "betrokkeneIdentificatie.geboortedatum": RegistrationAttribute.initiator_geboortedatum,
        "betrokkeneIdentificatie.geslachtsaanduiding": FieldConf(
            RegistrationAttribute.initiator_geslachtsaanduiding,
            transform=_gender_choices,
        ),
        # "betrokkeneIdentificatie.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        # Verblijfsadres for both Natuurlijk Persoon and Vestiging
        "betrokkeneIdentificatie.verblijfsadres.woonplaatsNaam": RegistrationAttribute.initiator_woonplaats,
        "betrokkeneIdentificatie.verblijfsadres.postcode": RegistrationAttribute.initiator_postcode,
        "betrokkeneIdentificatie.verblijfsadres.straatnaam": RegistrationAttribute.initiator_straat,
        "betrokkeneIdentificatie.verblijfsadres.huisnummer": RegistrationAttribute.initiator_huisnummer,
        "betrokkeneIdentificatie.verblijfsadres.huisletter": RegistrationAttribute.initiator_huisletter,
        "betrokkeneIdentificatie.verblijfsadres.huisnummertoevoeging": RegistrationAttribute.initiator_huisnummer_toevoeging,
        # Contactpersoon (NOT SUPPORTED BY ZGW APIs)
        # "betrokkeneIdentificatie.telefoonnummer": RegistrationAttribute.initiator_telefoonnummer,
        # "betrokkeneIdentificatie.emailadres": RegistrationAttribute.initiator_emailadres,
        # Vestiging
        "betrokkeneIdentificatie.vestigingsNummer": RegistrationAttribute.initiator_vestigingsnummer,
        "betrokkeneIdentificatie.handelsnaam": RegistrationAttribute.initiator_handelsnaam,
        # Identifiers
        "betrokkeneIdentificatie.inpBsn": FieldConf(
            submission_auth_info_attribute="bsn"
        ),
        # This field is not part of the StUF-ZDS standard.
        "betrokkeneIdentificatie._kvk": FieldConf(submission_auth_info_attribute="kvk"),
    }

    zaak_mapping = {
        "zaakgeometrie": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
    }

    @wrap_api_errors
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
        zgw = ZgwConfig.get_solo()
        zgw.apply_defaults_to(options)

        zaak_data = apply_data_mapping(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )

        _create_zaak = partial(
            create_zaak,
            options,
            payment_required=submission.payment_required,
            existing_reference=submission.public_registration_reference,
            **zaak_data,
        )
        zaak = execute_unless_result_exists(
            _create_zaak,
            submission,
            "intermediate.zaak",
        )
        submission_report = SubmissionReport.objects.get(submission=submission)
        document = execute_unless_result_exists(
            partial(
                create_report_document,
                submission.form.admin_name,
                submission_report,
                options,
            ),
            submission,
            "intermediate.documents.report.document",
        )
        execute_unless_result_exists(
            partial(relate_document, zaak["url"], document["url"]),
            submission,
            "intermediate.documents.report.relation",
        )

        rol_data = apply_data_mapping(
            submission, self.rol_mapping, REGISTRATION_ATTRIBUTE
        )

        betrokkene_identificatie = rol_data.get("betrokkeneIdentificatie", {})
        kvk = betrokkene_identificatie.pop("_kvk", None)

        if kvk:
            rol_data["betrokkeneType"] = "vestiging"
        else:
            rol_data["betrokkeneType"] = "natuurlijk_persoon"

        rol = execute_unless_result_exists(
            partial(create_rol, zaak, rol_data, options), submission, "intermediate.rol"
        )

        status = execute_unless_result_exists(
            partial(create_status, zaak), submission, "intermediate.status"
        )

        for attachment in submission.attachments:
            iot = attachment.informatieobjecttype or options["informatieobjecttype"]
            doc_options = {**options, "informatieobjecttype": iot}
            attachment_document = execute_unless_result_exists(
                partial(
                    create_attachment_document,
                    submission.form.admin_name,
                    attachment,
                    doc_options,
                ),
                submission,
                f"intermediate.documents.{attachment.id}.document",
            )
            execute_unless_result_exists(
                partial(relate_document, zaak["url"], attachment_document["url"]),
                submission,
                f"intermediate.documents.{attachment.id}.relation",
            )

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

    @wrap_api_errors
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
