import warnings
from datetime import datetime
from functools import partial, wraps
from io import BytesIO
from typing import Any, TypedDict

from django.urls import reverse
from django.utils.text import Truncator
from django.utils.translation import gettext, gettext_lazy as _

import requests
import structlog
from furl import furl
from glom import assign

from openforms.config.data import Action
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.clients.catalogi import (
    CatalogiClient,
    EigenschapSpecificatie,
    omschrijving_matcher,
)
from openforms.contrib.zgw.service import (
    DocumentOptions,
    create_attachment_document,
    create_report_document,
)
from openforms.emails.service import get_last_confirmation_email
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.typing import VariableValue
from openforms.utils.date import datetime_in_amsterdam
from openforms.utils.pdf import convert_html_to_pdf

from ...base import BasePlugin, PreRegistrationResult
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...contrib.objects_api.handlers.v1 import _get_variables_for_context
from ...exceptions import RegistrationFailed
from ...registry import register
from ...utils import execute_unless_result_exists
from .checks import check_config
from .client import get_catalogi_client, get_documents_client, get_zaken_client
from .models import ZGWApiGroupConfig
from .options import ZaakOptionsSerializer
from .typing import CatalogueOption, RegistrationOptions
from .utils import process_according_to_eigenschap_format

logger = structlog.stdlib.get_logger(__name__)


class VariablesProperties(TypedDict):
    component_key: str
    eigenschap: str


def get_property_mappings_from_submission(
    submission: Submission, mappings: list[VariablesProperties]
) -> dict[str, VariableValue]:
    """
    Extract the values from the submission and map onto the provided properties (eigenschappen).
    """

    # dict of {componentKey: eigenschap} mapping
    simple_mappings = {
        mapping["component_key"]: mapping["eigenschap"] for mapping in mappings
    }
    variable_values = submission.data

    property_mappings = {
        simple_mappings[key]: variable_values[key]
        for key in simple_mappings
        if key in variable_values
    }

    return property_mappings


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


class _Eigenschap(TypedDict):
    url: str
    specificatie: EigenschapSpecificatie


def _resolve_case_type(
    catalogi_client: CatalogiClient,
    catalogue: CatalogueOption,
    identification: str,
    submission_completed: datetime,
) -> str:
    version_valid_on = datetime_in_amsterdam(submission_completed).date()

    catalogus = catalogi_client.find_catalogus(**catalogue)
    if catalogus is None:
        raise RuntimeError(f"Could not resolve catalogue {catalogue}")
    versions = catalogi_client.find_case_types(
        catalogus=catalogus["url"],
        identification=identification,
        valid_on=version_valid_on,
    )

    if versions is None:
        raise RuntimeError(
            "Could not find a case type with identification "
            f"'{identification}' that is valid on "
            f"{version_valid_on.isoformat()}."
        )

    version = versions[0]
    return version["url"]


def _resolve_document_type(
    catalogi_client: CatalogiClient,
    catalogue: CatalogueOption,
    zaaktype_url: str,
    description: str,
    submission_completed: datetime,
):
    version_valid_on = datetime_in_amsterdam(submission_completed).date()

    catalogus = catalogi_client.find_catalogus(**catalogue)
    if catalogus is None:
        raise RuntimeError(f"Could not resolve catalogue {catalogue}")
    versions = catalogi_client.find_informatieobjecttypen(
        catalogus=catalogus["url"],
        description=description,
        valid_on=version_valid_on,
        within_casetype=zaaktype_url,
    )
    if versions is None:
        raise RuntimeError(
            "Could not find a document type with description "
            f"'{description}' in the case type that is valid on "
            f"{version_valid_on.isoformat()}."
        )

    # the client enforces there's a single version returned when a valid_on date is
    # passed.
    version = versions[0]
    return version["url"]


@register("zgw-create-zaak")
class ZGWRegistration(BasePlugin[RegistrationOptions]):
    verbose_name = _("ZGW API's")
    configuration_options = ZaakOptionsSerializer

    rol_mapping = {
        # Initiator
        # Natuurlijk Persoon
        "betrokkeneIdentificatie.voorletters": RegistrationAttribute.initiator_voorletters,
        "betrokkeneIdentificatie.voornamen": RegistrationAttribute.initiator_voornamen,
        "betrokkeneIdentificatie.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "betrokkeneIdentificatie.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "betrokkeneIdentificatie.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum,
            transform=lambda date: date.isoformat() if date else "",
        ),
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
        "betrokkeneIdentificatie.handelsnaam": FieldConf(
            attribute=RegistrationAttribute.initiator_handelsnaam,
            transform=lambda v: [v],
        ),
        "betrokkeneIdentificatie.kvkNummer": FieldConf(
            submission_auth_info_attribute="kvk"
        ),
        # Niet Natuurlijk Persoon
        "betrokkeneIdentificatie.statutaireNaam": RegistrationAttribute.initiator_handelsnaam,
        "betrokkeneIdentificatie.innNnpId": FieldConf(
            submission_auth_info_attribute="kvk"
        ),
        # Identifiers
        "betrokkeneIdentificatie.inpBsn": FieldConf(
            submission_auth_info_attribute="bsn"
        ),
        # Family members
        "partners": RegistrationAttribute.partners,
        "children": RegistrationAttribute.children,
    }

    zaak_mapping = {
        "zaakgeometrie": FieldConf(RegistrationAttribute.locatie_coordinaat),
    }

    @wrap_api_errors
    def pre_register_submission(
        self, submission: "Submission", options: RegistrationOptions
    ) -> PreRegistrationResult:
        """
        Create a Zaak, so that we can have a registration ID.

        Note: The Rol, Status, the documents for the files uploaded by the user in the form (attachments) and the
        confirmation report PDF will be added in the registration task (after the report has been generated).
        """
        zgw: ZGWApiGroupConfig = options["zgw_api_group"]
        zgw.apply_defaults_to(options)
        # help the type checker a little... it doesn't understand the mutations in
        # apply_defaults_to
        assert "organisatie_rsin" in options

        zaak_data = apply_data_mapping(
            submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
        )

        # resolve zaaktype to use
        if case_type_identification := options["case_type_identification"]:
            catalogue = options.get("catalogue")
            assert catalogue is not None  # enforced by validation
            with get_catalogi_client(zgw) as catalogi_client:
                zaaktype_url = _resolve_case_type(
                    catalogi_client,
                    catalogue,
                    case_type_identification,
                    submission.completed_on,
                )
        else:
            warnings.warn(
                "Using the zaaktype URL option is deprecated and will be removed in "
                "Open Forms 4.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            zaaktype_url = options["zaaktype"]

        with get_zaken_client(zgw) as zaken_client:
            _create_zaak = partial(
                zaken_client.create_zaak,
                zaaktype=zaaktype_url,
                omschrijving=Truncator(submission.form.name).chars(80),
                bronorganisatie=options["organisatie_rsin"],
                vertrouwelijkheidaanduiding=options.get(
                    "zaak_vertrouwelijkheidaanduiding", ""
                ),
                product_url=options["product_url"],
                payment_required=submission.payment_required,
                existing_reference=submission.public_registration_reference,
                **zaak_data,
            )
            zaak = execute_unless_result_exists(
                _create_zaak,
                submission,
                "intermediate.zaak",
            )

        return PreRegistrationResult(
            reference=zaak["identificatie"], data={"zaak": zaak}
        )

    @wrap_api_errors
    def register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict | None:
        """
        Add the PDF document with the submission data (confirmation report) to the zaak created during pre-registration.
        """
        zgw: ZGWApiGroupConfig = options["zgw_api_group"]
        zgw.apply_defaults_to(options)
        # help the type checker a little... it doesn't understand the mutations in
        # apply_defaults_to
        assert "organisatie_rsin" in options
        assert "doc_vertrouwelijkheidaanduiding" in options
        assert "auteur" in options

        result = submission.registration_result
        assert result, "Result should have been set by pre-registration"
        zaak = result["zaak"]

        submission_report = SubmissionReport.objects.get(submission=submission)
        initiator_rol_data = apply_data_mapping(
            submission, self.rol_mapping, REGISTRATION_ATTRIBUTE
        )

        # family members
        partners_rol_data = {}
        if RegistrationAttribute.partners in initiator_rol_data:
            partners_rol_data = initiator_rol_data.pop(
                RegistrationAttribute.partners, []
            )
        children_rol_data = {}
        if RegistrationAttribute.children in initiator_rol_data:
            children_rol_data = initiator_rol_data.pop(
                RegistrationAttribute.children, []
            )

        betrokkene_identificatie = initiator_rol_data.get("betrokkeneIdentificatie", {})
        kvk = betrokkene_identificatie.get("innNnpId")
        vestigingsnummer = betrokkene_identificatie.get("vestigingsNummer")

        if kvk and vestigingsnummer:
            initiator_rol_data["betrokkeneType"] = "vestiging"
        elif kvk:
            initiator_rol_data["betrokkeneType"] = "niet_natuurlijk_persoon"
        else:
            initiator_rol_data["betrokkeneType"] = "natuurlijk_persoon"

        if verblijfsadres := betrokkene_identificatie.get("verblijfsadres"):
            # GH-4191: Required and min length of 1 char, but we don't have a way to get
            # this value without trying to look up the other details in the BAG API,
            # which would make BAG integration mandatory... this doesn't seem
            # intentional. An issue was opened with VNG:
            # https://github.com/VNG-Realisatie/gemma-zaken/issues/2451
            #
            # So, we put a dummy value in here that can be ignored by the received
            # party...
            verblijfsadres["aoaIdentificatie"] = "OFWORKAROUND"

        with (
            get_documents_client(zgw) as documents_client,
            get_zaken_client(zgw) as zaken_client,
            get_catalogi_client(zgw) as catalogi_client,
        ):
            # resolve (default) document type to use
            if document_type_description := options["document_type_description"]:
                catalogue = options.get("catalogue")
                assert catalogue is not None  # enforced by validation
                informatieobjecttype_url = _resolve_document_type(
                    catalogi_client,
                    catalogue=catalogue,
                    zaaktype_url=zaak["zaaktype"],
                    description=document_type_description,
                    submission_completed=submission.completed_on,
                )
            else:
                warnings.warn(
                    "Using the informatieobjecttype URL option is deprecated and will "
                    "be removed in Open Forms 4.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                informatieobjecttype_url = options["informatieobjecttype"]

            result["informatieobjecttype_url"] = informatieobjecttype_url

            # Upload the summary PDF
            pdf_options: DocumentOptions = {
                "informatieobjecttype": informatieobjecttype_url,
                "organisatie_rsin": options["organisatie_rsin"],
                "auteur": options["auteur"],
                "doc_vertrouwelijkheidaanduiding": options[
                    "doc_vertrouwelijkheidaanduiding"
                ],
            }
            summary_pdf_document = execute_unless_result_exists(
                partial(
                    create_report_document,
                    client=documents_client,
                    name=submission.form.admin_name,
                    submission_report=submission_report,
                    options=pdf_options,
                    language=submission_report.submission.language_code,
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

            initiator_rol = execute_unless_result_exists(
                partial(
                    zaken_client.create_rol,
                    catalogi_client=catalogi_client,
                    zaak=zaak,
                    betrokkene=initiator_rol_data,
                ),
                submission,
                "intermediate.initiator_rol",
            )

            # We may have multiple roles that need to be created, for now this is needed
            # for custom partners and children components
            partners_rollen = []
            if partners_rol_data:
                for index, data in enumerate(partners_rol_data):
                    partners_roltype_omschrijving = options["partners_roltype"]
                    partners_description = options["partners_description"]
                    roltypen = catalogi_client.list_roltypen(
                        zaaktype=zaak["zaaktype"],
                        matcher=omschrijving_matcher(partners_roltype_omschrijving),
                    )
                    roltype = roltypen[0]

                    data.update(
                        {
                            "roltype": roltype["url"],
                            "betrokkeneType": "natuurlijk_persoon",
                            "roltoelichting": partners_description
                            or "natuurlijk_persoon",
                            "betrokkeneIdentificatie": {
                                "inpBsn": data.get("bsn") or "",
                                "voorvoegselGeslachtsnaam": data.get("affixes") or "",
                                "voorletters": data.get("initials") or "",
                                "geslachtsnaam": data.get("lastName") or "",
                                "voornamen": data.get("firstNames") or "",
                                "geboortedatum": data.get("dateOfBirth").isoformat()
                                or "",
                            },
                        }
                    )

                    partner_rol = execute_unless_result_exists(
                        partial(
                            zaken_client.create_rol,
                            catalogi_client=catalogi_client,
                            zaak=zaak,
                            betrokkene=data,
                        ),
                        submission,
                        f"intermediate.partner_rol.{index + 1}",
                    )
                    partners_rollen.append(partner_rol)

            children_rollen = []
            if children_rol_data:
                for index, data in enumerate(children_rol_data):
                    if data.get("selected") not in (None, True):
                        continue

                    children_roltype_omschrijving = options["children_roltype"]
                    children_description = options["children_description"]
                    roltypen = catalogi_client.list_roltypen(
                        zaaktype=zaak["zaaktype"],
                        matcher=omschrijving_matcher(children_roltype_omschrijving),
                    )
                    roltype = roltypen[0]

                    data.update(
                        {
                            "roltype": roltype["url"],
                            "betrokkeneType": "natuurlijk_persoon",
                            "betrokkeneIdentificatie": {
                                "inpBsn": data.get("bsn"),
                                "voorvoegselGeslachtsnaam": data.get("affixes"),
                                "voorletters": data.get("initials"),
                                "geslachtsnaam": data.get("lastName"),
                                "voornamen": data.get("firstNames"),
                                "geboortedatum": data.get("dateOfBirth").isoformat(),
                                "roltoelichting": children_description,
                            },
                        }
                    )

                    child_rol = execute_unless_result_exists(
                        partial(
                            zaken_client.create_rol,
                            catalogi_client=catalogi_client,
                            zaak=zaak,
                            betrokkene=data,
                        ),
                        submission,
                        f"intermediate.child_rol.{index + 1}",
                    )
                    children_rollen.append(child_rol)

            medewerker_rol: dict[str, Any] | None = None
            if submission.has_registrator:
                assert submission.registrator

                roltype_omschrijving = options.get("medewerker_roltype")
                assert roltype_omschrijving
                roltypen = catalogi_client.list_roltypen(
                    zaaktype=zaak["zaaktype"],
                    matcher=omschrijving_matcher(roltype_omschrijving),
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
                iot = attachment.informatieobjecttype or informatieobjecttype_url
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
                doc_options: DocumentOptions = {
                    "informatieobjecttype": iot,
                    "organisatie_rsin": bronorganisatie,
                    "auteur": options["auteur"],
                    "doc_vertrouwelijkheidaanduiding": options[
                        "doc_vertrouwelijkheidaanduiding"
                    ],
                    "titel": titel,
                }

                # this helps the type checker in narrowing the type
                # and expressing that it should not happen that submission.completed_on is not set
                assert submission.completed_on is not None
                doc_options["ontvangstdatum"] = (
                    datetime_in_amsterdam(submission.completed_on).date().isoformat()
                )

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
                        language=attachment.submission_step.submission.language_code,  # assume same as submission
                    ),
                    submission,
                    f"intermediate.documents.{attachment.id}.document",  # type: ignore
                )
                execute_unless_result_exists(
                    partial(
                        zaken_client.relate_document,
                        zaak=zaak,
                        document=attachment_document,
                    ),
                    submission,
                    f"intermediate.documents.{attachment.id}.relation",  # type: ignore
                )

            result.update(
                {
                    "document": summary_pdf_document,
                    "status": status,
                    "initiator_rol": initiator_rol,
                }
            )

        if medewerker_rol:
            result["medewerker_rol"] = medewerker_rol

        if partners_rol_data:
            result["partners_rollen"] = partners_rollen
        if children_rol_data:
            result["children_rollen"] = children_rollen

        # Register submission to Objects API if configured
        if (
            options["objects_api_group"]
            and (object_type := options.get("objecttype"))
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
                partial(catalogi_client.list_eigenschappen, zaak["zaaktype"]),
                submission,
                "intermediate.zaaktype_eigenschappen",
            )

            retrieved_eigenschappen: dict[str, _Eigenschap] = {
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

    @wrap_api_errors
    def update_payment_status(
        self, submission: Submission, options: RegistrationOptions
    ):
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
                _("Manage API groups"),
                reverse("admin:zgw_apis_zgwapigroupconfig_changelist"),
            ),
        ]

    def register_submission_to_objects_api(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict:
        assert "objecttype" in options
        assert "objecttype_version" in options
        assert "content_json" in options

        object_mapping = {
            "geometry": FieldConf(RegistrationAttribute.locatie_coordinaat),
        }

        context = {
            "_submission": submission,
            "productaanvraag_type": "ProductAanvraag",
            "variables": _get_variables_for_context(submission),
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
            },
        }

        data = render_to_json(options["content_json"], context)
        assert isinstance(data, dict)
        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options.get("objecttype_version", 1),
        )

        apply_data_mapping(
            submission,
            object_mapping,
            REGISTRATION_ATTRIBUTE,
            record_data,  # pyright: ignore[reportArgumentType]
        )

        api_group = options["objects_api_group"]
        assert api_group is not None
        with get_objects_client(api_group) as objects_client:
            response = execute_unless_result_exists(
                partial(
                    objects_client.create_object,
                    objecttype_url=options["objecttype"],
                    record_data=record_data,
                ),
                submission,
                "intermediate.objects_api_object",
            )

            return response

    @wrap_api_errors
    def update_registration_with_confirmation_email(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict | None:
        logger.info(
            "update_registration_with_confirmation_email_started", options=options
        )

        if not submission.confirmation_email_sent:
            logger.info(
                "update_registration_with_confirmation_email_skipped",
                reason="no_confirmation_email_sent",
            )
            return None

        res = get_last_confirmation_email(submission)
        if res is None:
            logger.info(
                "update_registration_with_confirmation_email_aborted",
                reason="no_confirmation_email_found",
            )
            raise RegistrationFailed("Confirmation email was not found")
        html, message_id = res

        result = submission.registration_result
        assert result
        assert "informatieobjecttype_url" in result, (
            "Should be set during main registration"
        )

        zgw: ZGWApiGroupConfig = options["zgw_api_group"]
        zgw.apply_defaults_to(options)
        # help the type checker a little... it doesn't understand the mutations in
        # apply_defaults_to
        assert "organisatie_rsin" in options
        assert "doc_vertrouwelijkheidaanduiding" in options
        assert "auteur" in options

        assert submission.completed_on is not None
        date = datetime_in_amsterdam(submission.completed_on).date().isoformat()

        # Generate email
        content = BytesIO(convert_html_to_pdf(html))

        # Create a document
        with get_documents_client(zgw) as documents_client:
            logger.debug("creating_confirmation_email_document")
            document = execute_unless_result_exists(
                partial(
                    documents_client.create_document,
                    informatieobjecttype=result["informatieobjecttype_url"],
                    bronorganisatie=options["organisatie_rsin"],
                    title="Bevestigingsmail",
                    author=options["auteur"],
                    language=submission.language_code,
                    format="application/pdf",
                    content=content,
                    status="definitief",
                    filename="bevestigingsmail.pdf",
                    description="De bevestigingsmail die naar de initiator is verstuurd.",
                    received_date=date,
                    vertrouwelijkheidaanduiding=(
                        options["doc_vertrouwelijkheidaanduiding"]
                    ),
                ),
                submission,
                f"intermediate.confirmation_emails.{message_id}.document",
            )

        # Relate the document to the zaak
        with get_zaken_client(zgw) as zaken_client:
            logger.debug("relating_confirmation_email_document")
            execute_unless_result_exists(
                partial(
                    zaken_client.relate_document,
                    zaak=result["zaak"],
                    document=document,
                ),
                submission,
                f"intermediate.confirmation_emails.{message_id}.relation",
            )

        return result
