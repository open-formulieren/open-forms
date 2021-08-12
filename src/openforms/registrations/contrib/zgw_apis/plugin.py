from typing import Optional

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.registrations.base import BasePlugin
from openforms.registrations.constants import (
    REGISTRATION_ATTRIBUTE,
    RegistrationAttribute,
)
from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.registrations.contrib.zgw_apis.service import (
    create_attachment,
    create_document,
    create_rol,
    create_status,
    create_zaak,
    relate_document,
)
from openforms.registrations.registry import register
from openforms.submissions.mapping import FieldConf, apply_data_mapping
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

        zaak = create_zaak(options)

        submission_report = SubmissionReport.objects.get(submission=submission)
        document = create_document(submission.form.name, submission_report, options)
        relate_document(zaak["url"], document["url"])

        rol_data = apply_data_mapping(
            submission, self.rol_mapping, REGISTRATION_ATTRIBUTE
        )
        rol = create_rol(zaak, rol_data, options)

        # for now create generic status
        status = create_status(zaak)

        for attachment in submission.attachments:
            attachment = create_attachment(submission.form.name, attachment, options)
            relate_document(zaak["url"], attachment["url"])

        result = {
            "zaak": zaak,
            "document": document,
            "status": status,
            "rol": rol,
        }
        return result
