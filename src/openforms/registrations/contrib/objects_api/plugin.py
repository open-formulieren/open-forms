import logging
from functools import partial
from typing import Any, Dict, NoReturn

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.clients import DocumentenClient
from openforms.contrib.zgw.clients.utils import get_today
from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.registrations.utils import execute_unless_result_exists
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf
from openforms.submissions.models import Submission, SubmissionReport
from openforms.submissions.public_references import set_submission_reference
from openforms.translations.utils import to_iso639_2b
from openforms.variables.utils import get_variables_for_context

from ...base import BasePlugin
from ...constants import RegistrationAttribute
from ...exceptions import NoSubmissionReference
from ...registry import register
from .checks import check_config
from .client import get_documents_client, get_objects_client
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig
from .utils import get_payment_context_data

PLUGIN_IDENTIFIER = "objects_api"

logger = logging.getLogger(__name__)


def _point_coordinate(value):
    if not value or not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"type": "Point", "coordinates": [value[0], value[1]]}


def build_options(plugin_options: dict, key_mapping: dict) -> dict:
    """
    Construct options from plugin options dict, allowing renaming of keys
    """
    options = {
        new_key: plugin_options[key_in_opts]
        for new_key, key_in_opts in key_mapping.items()
        if key_in_opts in plugin_options
    }
    return options


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIRegistration(BasePlugin):
    verbose_name = _("Objects API registration")
    configuration_options = ObjectsAPIOptionsSerializer

    object_mapping = {
        "record.geometry": FieldConf(
            RegistrationAttribute.locatie_coordinaat, transform=_point_coordinate
        ),
    }

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Dict[str, Any]:
        """Register a submission using the ObjectsAPI backend

        The creation of submission documents (report, attachment, csv) makes use of ZGW
        service functions (e.g. :func:`create_report_document`) and involves a mapping
        (and in some cases renaming) of variables which would otherwise not be
        accessible from here. For example, 'vertrouwelijkheidaanduiding' must be named
        'doc_vertrouwelijkheidaanduiding' because this is what the ZGW service functions
        use."""
        config = ObjectsAPIConfig.get_solo()
        assert isinstance(config, ObjectsAPIConfig)
        config.apply_defaults_to(options)

        # Prepare all documents to relate to the Objects API record
        with get_documents_client() as documents_client:
            # Create the document for the PDF summary
            submission_report = SubmissionReport.objects.get(submission=submission)
            submission_report_options = build_options(
                options,
                {
                    "informatieobjecttype": "informatieobjecttype_submission_report",
                    "organisatie_rsin": "organisatie_rsin",
                    "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                },
            )

            document = create_report_document(
                client=documents_client,
                name=submission.form.admin_name,
                submission_report=submission_report,
                options=submission_report_options,
            )

            # Register the attachments
            # TODO turn attachments into dictionary when giving users more options then
            # just urls.
            attachments = []
            for attachment in submission.attachments:
                attachment_options = build_options(
                    options,
                    {
                        "informatieobjecttype": "informatieobjecttype_attachment",  # Different IOT than for the report
                        "organisatie_rsin": "organisatie_rsin",
                        "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                    },
                )

                component_overwrites = {
                    "doc_vertrouwelijkheidaanduiding": attachment.doc_vertrouwelijkheidaanduiding,
                    "titel": attachment.titel,
                    "organisatie_rsin": attachment.bronorganisatie,
                    "informatieobjecttype": attachment.informatieobjecttype,
                }

                for key, value in component_overwrites.items():
                    if value:
                        attachment_options[key] = value

                attachment_document = create_attachment_document(
                    client=documents_client,
                    name=submission.form.admin_name,
                    submission_attachment=attachment,
                    options=attachment_options,
                )
                attachments.append(attachment_document["url"])

            # Create the CSV submission export, if requested.
            # If no CSV is being uploaded, then `assert csv_url == ""` applies.
            csv_url = register_submission_csv(submission, options, documents_client)

        context = {
            "_submission": submission,
            "productaanvraag_type": options["productaanvraag_type"],
            "payment": get_payment_context_data(submission),
            "variables": get_variables_for_context(submission),
            # Github issue #661, nested for namespacing note: other templates and context expose all submission
            # variables in the top level namespace, but that is due for refactor
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
                "uploaded_attachment_urls": attachments,
                "pdf_url": document["url"],
                "csv_url": csv_url,
            },
        }

        object_data = prepare_data_for_registration(
            submission, context, options, self.object_mapping
        )

        with get_objects_client() as objects_client:
            response = execute_unless_result_exists(
                partial(objects_client.create_object, object_data=object_data),
                submission,
                "intermediate.objects_api_object",
            )

        return response

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Object API plugin does not emit a reference")

    def check_config(self):
        check_config()

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:registrations_objects_api_objectsapiconfig_change",
                    args=(ObjectsAPIConfig.singleton_instance_id,),
                ),
            ),
        ]

    def pre_register_submission(self, submission: "Submission", options: dict) -> None:
        set_submission_reference(submission)

    def get_custom_templatetags_libraries(self) -> list[str]:
        prefix = "openforms.registrations.contrib.objects_api.templatetags.registrations.contrib"
        return [
            f"{prefix}.objects_api.json_tags",
        ]

    def update_payment_status(self, submission: "Submission", options: dict) -> None:
        config = ObjectsAPIConfig.get_solo()
        assert isinstance(config, ObjectsAPIConfig)
        config.apply_defaults_to(options)

        if not options["payment_status_update_json"]:
            logger.warning(
                "Skipping payment status update because no template was configured."
            )
            return

        context = {
            "variables": get_variables_for_context(submission),
            "payment": get_payment_context_data(submission),
        }

        updated_record_data = render_to_json(
            options["payment_status_update_json"], context
        )
        updated_object_data = {
            "record": {
                "data": updated_record_data,
                "startAt": get_today(),
            },
        }

        object_url = submission.registration_result["url"]
        with get_objects_client() as objects_client:
            response = objects_client.patch(
                url=object_url,
                json=updated_object_data,
                headers={"Content-Crs": "EPSG:4326"},
            )
            response.raise_for_status()


def register_submission_csv(
    submission: Submission,
    options: dict,
    documents_client: DocumentenClient,
) -> str:
    if not options.get("upload_submission_csv", False):
        return ""

    if not options["informatieobjecttype_submission_csv"]:
        return ""

    submission_csv_options = build_options(
        options,
        {
            "informatieobjecttype": "informatieobjecttype_submission_csv",
            "organisatie_rsin": "organisatie_rsin",
            "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
            "auteur": "auteur",
        },
    )
    qs = Submission.objects.filter(pk=submission.pk).select_related("auth_info")
    submission_csv = create_submission_export(qs).export("csv")  # type: ignore

    language_code_2b = to_iso639_2b(submission.language_code)
    submission_csv_document = create_csv_document(
        client=documents_client,
        name=f"{submission.form.admin_name} (csv)",
        csv_data=submission_csv,
        options=submission_csv_options,
        language=language_code_2b,
    )

    return submission_csv_document["url"]
