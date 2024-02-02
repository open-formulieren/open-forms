import logging
from functools import partial, wraps
from typing import Any, TypedDict

from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

import requests
from furl import furl
from glom import assign
from rest_framework import serializers
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.config.data import Action
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.zgw.clients.catalogi import omschrijving_matcher
from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_report_document,
)
from openforms.formio.validators import variable_key_validator
from openforms.registrations.contrib.objects_api.client import get_objects_client
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin
from openforms.variables.utils import get_variables_for_context

from ...base import BasePlugin
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...exceptions import RegistrationFailed
from ...registry import register
from ...utils import execute_unless_result_exists
from .checks import check_config
from .client import get_catalogi_client, get_documents_client, get_zaken_client
from .models import ZGWApiGroupConfig, ZgwConfig
from .utils import process_according_to_eigenschap_format

logger = logging.getLogger(__name__)


class VariablesProperties(TypedDict):
    component_key: str
    eigenschap: str


def get_property_mappings_from_submission(
    submission: Submission, mappings: list[VariablesProperties]
) -> dict[str, Any]:
    """
    Extract the values from the submission and map onto the provided properties (eigenschappen).
    """
    property_mappings = {}

    # dict of {componentKey: eigenschap} mapping
    simple_mappings = {
        mapping["component_key"]: mapping["eigenschap"] for mapping in mappings
    }

    variable_values = submission.submissionvaluevariable_set.filter(
        key__in=simple_mappings
    ).values_list("key", "value")

    for key, form_value in variable_values:
        eigenschap = simple_mappings[key]
        property_mappings[eigenschap] = form_value

    return property_mappings


class MappedVariablePropertySerializer(serializers.Serializer):
    component_key = serializers.CharField(
        label=_("Component key"),
        validators=[variable_key_validator],
        help_text=_("Key of the form variable to take the value from."),
    )
    eigenschap = serializers.CharField(
        label=_("Property"),
        max_length=20,
        help_text=_(
            "Name of the property on the case type to which the variable will be "
            "mapped."
        ),
    )


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.all(),
        help_text=_("Which ZGW API set to use."),  # type: ignore
        label=_("ZGW API set"),  # type: ignore
        required=False,
    )
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
    zaak_vertrouwelijkheidaanduiding = serializers.ChoiceField(
        label=_("Vertrouwelijkheidaanduiding"),
        required=False,
        choices=VertrouwelijkheidsAanduidingen.choices,
        help_text=_(
            "Indication of the level to which extend the dossier of the ZAAK is meant to be public."
        ),
    )
    medewerker_roltype = serializers.CharField(
        required=False,
        help_text=_(
            "Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company."
        ),
    )

    # Objects API
    objecttype = serializers.URLField(
        label=_("objects API - objecttype"),
        help_text=_(
            "URL that points to the ProductAanvraag objecttype in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
        required=False,
    )
    objecttype_version = serializers.IntegerField(
        label=_("objects API - objecttype version"),
        help_text=_("Version of the objecttype in the Objecttypes API"),
        required=False,
    )
    content_json = serializers.CharField(
        label=_("objects API - JSON content field"),
        help_text=_(
            "JSON template for the body of the request sent to the Objects API."
        ),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        required=False,
    )

    # Eigenschappen
    property_mappings = MappedVariablePropertySerializer(
        many=True,
        label=_("Variable-to-property mappings"),
        required=False,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # First checking that a ZGWApiGroupConfig is available:
        if attrs.get("zgw_api_group") is None:
            config = ZgwConfig.get_solo()
            assert isinstance(config, ZgwConfig)
            if config.default_zgw_api_group is None:
                raise serializers.ValidationError(
                    {
                        "zgw_api_group": _(
                            "No ZGW API set was configured on the form and no default was specified globally."
                        )
                    },
                    code="invalid",
                )

        # We know it exists thanks to the previous check
        group_config = ZGWRegistration.get_zgw_config(attrs)

        # Make sure the property (eigenschap) related to the zaaktype exists
        if mappings := attrs.get("property_mappings"):
            with get_catalogi_client(group_config) as client:
                eigenschappen = client.list_eigenschappen(
                    zaaktype=attrs.get("zaaktype") or group_config.zaaktype
                )
                retrieved_eigenschappen = {
                    eigenschap["naam"]: eigenschap["url"]
                    for eigenschap in eigenschappen
                }

                errors = []
                for mapping in mappings:
                    if mapping["eigenschap"] not in retrieved_eigenschappen:
                        errors.append(
                            _(
                                "Could not find a property with the name "
                                "'{property_name}' related to the zaaktype."
                            ).format(property_name=mapping["eigenschap"])
                        )

                if errors:
                    raise serializers.ValidationError(
                        {"property_mappings": errors}, code="invalid"
                    )

        if not ("medewerker_roltype" in attrs and "zaaktype" in attrs):
            return attrs

        with get_catalogi_client(group_config) as client:
            roltypen = client.list_roltypen(
                zaaktype=attrs["zaaktype"],
                matcher=omschrijving_matcher(attrs["medewerker_roltype"]),
            )

        if not roltypen:
            raise serializers.ValidationError(
                {
                    "medewerker_roltype": _(
                        "Could not find a roltype with this description related to the zaaktype."
                    )
                },
                code="invalid",
            )

        return attrs


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
        except requests.RequestException as exc:
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
        "betrokkeneIdentificatie.verblijfsadres.wplWoonplaatsNaam": RegistrationAttribute.initiator_woonplaats,
        "betrokkeneIdentificatie.verblijfsadres.aoaPostcode": RegistrationAttribute.initiator_postcode,
        "betrokkeneIdentificatie.verblijfsadres.gorOpenbareRuimteNaam": RegistrationAttribute.initiator_straat,
        "betrokkeneIdentificatie.verblijfsadres.aoaHuisnummer": RegistrationAttribute.initiator_huisnummer,
        "betrokkeneIdentificatie.verblijfsadres.aoaHuisletter": RegistrationAttribute.initiator_huisletter,
        "betrokkeneIdentificatie.verblijfsadres.aoaHuisnummertoevoeging": RegistrationAttribute.initiator_huisnummer_toevoeging,
        # Contactpersoon (NOT SUPPORTED BY ZGW APIs)
        # "betrokkeneIdentificatie.telefoonnummer": RegistrationAttribute.initiator_telefoonnummer,
        # "betrokkeneIdentificatie.emailadres": RegistrationAttribute.initiator_emailadres,
        # Vestiging
        "betrokkeneIdentificatie.vestigingsNummer": RegistrationAttribute.initiator_vestigingsnummer,
        "betrokkeneIdentificatie.handelsnaam": RegistrationAttribute.initiator_handelsnaam,
        # Niet Natuurlijk Persoon
        "betrokkeneIdentificatie.statutaireNaam": RegistrationAttribute.initiator_handelsnaam,
        "betrokkeneIdentificatie.innNnpId": FieldConf(
            submission_auth_info_attribute="kvk"
        ),
        # Identifiers
        "betrokkeneIdentificatie.inpBsn": FieldConf(
            submission_auth_info_attribute="bsn"
        ),
    }

    zaak_mapping = {
        "zaakgeometrie": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
    }

    @staticmethod
    def get_zgw_config(options: dict) -> ZGWApiGroupConfig:
        zgw = options.get("zgw_api_group")
        if zgw is None:
            config = ZgwConfig.get_solo()
            assert isinstance(config, ZgwConfig)
            zgw = config.default_zgw_api_group
        return zgw

    @wrap_api_errors
    def pre_register_submission(self, submission: "Submission", options: dict) -> None:
        """
        Create a Zaak, so that we can have a registration ID.

        Note: The Rol, Status, the documents for the files uploaded by the user in the form (attachments) and the
        confirmation report PDF will be added in the registration task (after the report has been generated).
        """
        zgw = self.get_zgw_config(options)
        zgw.apply_defaults_to(options)

        zaak_data = apply_data_mapping(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )

        with get_zaken_client(zgw) as zaken_client:
            _create_zaak = partial(
                zaken_client.create_zaak,
                zaaktype=options["zaaktype"],
                bronorganisatie=options["organisatie_rsin"],
                vertrouwelijkheidaanduiding=options.get(
                    "zaak_vertrouwelijkheidaanduiding", ""
                ),
                payment_required=submission.payment_required,
                existing_reference=submission.public_registration_reference,
                **zaak_data,
            )
            zaak = execute_unless_result_exists(
                _create_zaak,
                submission,
                "intermediate.zaak",
            )

        result = {"zaak": zaak}
        submission.registration_result.update(result)
        submission.public_registration_reference = self.get_reference_from_result(
            result
        )
        submission.save()

    @wrap_api_errors
    def register_submission(self, submission: Submission, options: dict) -> dict | None:
        """
        Add the PDF document with the submission data (confirmation report) to the zaak created during pre-registration.
        """
        zgw = self.get_zgw_config(options)
        zgw.apply_defaults_to(options)

        result = submission.registration_result
        assert result, "Result should have been set by pre-registration"
        zaak = result["zaak"]

        submission_report = SubmissionReport.objects.get(submission=submission)
        rol_data = apply_data_mapping(
            submission, self.rol_mapping, REGISTRATION_ATTRIBUTE
        )

        betrokkene_identificatie = rol_data.get("betrokkeneIdentificatie", {})
        kvk = betrokkene_identificatie.get("innNnpId")
        vestigingsnummer = betrokkene_identificatie.get("vestigingsNummer")

        if kvk and vestigingsnummer:
            rol_data["betrokkeneType"] = "vestiging"
        elif kvk:
            rol_data["betrokkeneType"] = "niet_natuurlijk_persoon"
        else:
            rol_data["betrokkeneType"] = "natuurlijk_persoon"

        with (
            get_documents_client(zgw) as documents_client,
            get_zaken_client(zgw) as zaken_client,
            get_catalogi_client(zgw) as catalogi_client,
        ):
            # Upload the summary PDF
            summary_pdf_document = execute_unless_result_exists(
                partial(
                    create_report_document,
                    client=documents_client,
                    name=submission.form.admin_name,
                    submission_report=submission_report,
                    options=options,
                ),
                submission,
                "intermediate.documents.report.document",
            )

            # Relate summary PDF
            execute_unless_result_exists(
                partial(
                    zaken_client.relate_document,
                    zaak=zaak,
                    document=summary_pdf_document,
                ),
                submission,
                "intermediate.documents.report.relation",
            )

            rol = execute_unless_result_exists(
                partial(
                    zaken_client.create_rol,
                    catalogi_client=catalogi_client,
                    zaak=zaak,
                    betrokkene=rol_data,
                ),
                submission,
                "intermediate.rol",
            )

            if submission.has_registrator:
                assert submission.registrator

                roltypen = catalogi_client.list_roltypen(
                    zaaktype=zaak["zaaktype"],
                    matcher=omschrijving_matcher(options["medewerker_roltype"]),
                )
                roltype = roltypen[0]

                registrator_rol_data = {
                    "betrokkeneType": "medewerker",
                    "roltype": roltype["url"],
                    "roltoelichting": gettext(
                        "Employee who registered the case on behalf of the customer."
                    ),
                    "betrokkeneIdentificatie": {
                        "identificatie": submission.registrator.value,
                    },
                }

                medewerker_rol = execute_unless_result_exists(
                    partial(
                        zaken_client.create_rol,
                        catalogi_client=catalogi_client,
                        zaak=zaak,
                        betrokkene=registrator_rol_data,
                    ),
                    submission,
                    "intermediate.medewerker_rol",
                )

            status = execute_unless_result_exists(
                partial(
                    zaken_client.create_status,
                    catalogi_client=catalogi_client,
                    zaak=zaak,
                ),
                submission,
                "intermediate.status",
            )

            # TODO: threading? asyncio?
            for attachment in submission.attachments:
                # collect attributes of the attachment and add them to the configuration
                # attribute names conform to the Documenten API specification
                iot = attachment.informatieobjecttype or options["informatieobjecttype"]
                bronorganisatie = (
                    attachment.bronorganisatie or options["organisatie_rsin"]
                )
                vertrouwelijkheidaanduiding = (
                    attachment.doc_vertrouwelijkheidaanduiding
                    or options["doc_vertrouwelijkheidaanduiding"]
                )
                # `titel` should be a non-empty string
                # `get_display_name` is used to enforce this
                titel = attachment.titel or options.get(
                    "titel", attachment.get_display_name()
                )
                doc_options = {
                    **options,
                    "informatieobjecttype": iot,
                    "organisatie_rsin": bronorganisatie,
                    "titel": titel,
                }
                if vertrouwelijkheidaanduiding:
                    doc_options["doc_vertrouwelijkheidaanduiding"] = (
                        vertrouwelijkheidaanduiding
                    )

                attachment_document = execute_unless_result_exists(
                    partial(
                        create_attachment_document,
                        client=documents_client,
                        name=submission.form.admin_name,
                        submission_attachment=attachment,
                        options=doc_options,
                    ),
                    submission,
                    f"intermediate.documents.{attachment.id}.document",
                )
                execute_unless_result_exists(
                    partial(
                        zaken_client.relate_document,
                        zaak=zaak,
                        document=attachment_document,
                    ),
                    submission,
                    f"intermediate.documents.{attachment.id}.relation",
                )

            result.update(
                {
                    "document": summary_pdf_document,
                    "status": status,
                    "rol": rol,
                }
            )

        if submission.has_registrator:
            result["medewerker_rol"] = medewerker_rol

        # Register submission to Objects API if configured
        if (
            (object_type := options.get("objecttype"))
            and (object_type_version := options.get("objecttype_version"))
            and options.get("content_json")
        ):
            result["objects_api_object"] = execute_unless_result_exists(
                partial(self.register_submission_to_objects_api, submission, options),
                submission,
                "intermediate.objects_api_object",
            )

            # connect the zaak with the object
            objecttype_version = (
                furl(object_type) / "versions" / str(object_type_version)
            )

            result["zaakobject"] = execute_unless_result_exists(
                partial(
                    zaken_client.create_zaakobject,
                    zaak,
                    result["objects_api_object"]["url"],
                    objecttype_version.url,
                ),
                submission,
                "intermediate.objects_api_zaakobject",
            )

        # Map variables to case eigenschappen (if mappings are defined)
        if variables_properties := options.get("property_mappings"):
            property_mappings = get_property_mappings_from_submission(
                submission, variables_properties
            )

            eigenschappen = execute_unless_result_exists(
                partial(catalogi_client.list_eigenschappen, options["zaaktype"]),
                submission,
                "intermediate.zaaktype_eigenschappen",
            )

            retrieved_eigenschappen = {
                eigenschap["naam"]: {
                    "url": eigenschap["url"],
                    "specificatie": eigenschap["specificatie"],
                }
                for eigenschap in eigenschappen
            }

            for key, value in property_mappings.items():
                if key in retrieved_eigenschappen:
                    processed_value = process_according_to_eigenschap_format(
                        retrieved_eigenschappen[key]["specificatie"], value
                    )

                    eigenschap_url = furl(retrieved_eigenschappen[key].get("url"))
                    eigenschap_uuid = eigenschap_url.path.segments[-1]

                    created_zaakeigenschap = execute_unless_result_exists(
                        partial(
                            zaken_client.create_zaakeigenschap,
                            zaak,
                            {
                                "eigenschap": eigenschap_url.url,
                                "waarde": processed_value,
                            },
                        ),
                        submission,
                        f"intermediate.zaakeigenschap.{eigenschap_uuid}",
                    )

                    assign(
                        result,
                        f"zaakeigenschappen.{eigenschap_uuid}",
                        created_zaakeigenschap,
                        missing=dict,
                    )

        submission.registration_result = result
        submission.save()
        return result

    def get_reference_from_result(self, result: dict[str, Any]) -> str:
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
    def update_payment_status(self, submission: Submission, options: dict):
        zgw = options["zgw_api_group"]
        assert submission.registration_result
        zaak = submission.registration_result["zaak"]
        with get_zaken_client(zgw) as zaken_client:
            zaken_client.set_payment_status(zaak)

    def check_config(self):
        check_config()

    def get_config_actions(self) -> list[Action]:
        return [
            (
                gettext("Configuration"),
                reverse(
                    "admin:zgw_apis_zgwapigroupconfig_changelist",
                ),
            ),
        ]

    def register_submission_to_objects_api(
        self, submission: Submission, options: dict
    ) -> dict:
        object_mapping = {
            "record.geometry": FieldConf(
                RegistrationAttribute.locatie_coordinaat,
                transform=_point_coordinate,
            ),
        }

        context = {
            "_submission": submission,
            "productaanvraag_type": "ProductAanvraag",
            "variables": get_variables_for_context(submission),
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
            },
        }

        object_data = prepare_data_for_registration(
            submission, context, options, object_mapping
        )

        with get_objects_client() as objects_client:
            response = execute_unless_result_exists(
                partial(objects_client.create_object, object_data=object_data),
                submission,
                "intermediate.objects_api_object",
            )

            return response
