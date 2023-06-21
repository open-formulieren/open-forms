import json
import logging
import sys
from datetime import date
from typing import Any, Dict, NoReturn

from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from zgw_consumers.client import ZGWClient

from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.submissions.public_references import set_submission_reference
from openforms.template import openforms_backend, render_from_string
from openforms.translations.utils import to_iso639_2b
from openforms.variables.utils import get_variables_for_context

from ...base import BasePlugin
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...exceptions import NoSubmissionReference
from ...registry import register
from .checks import check_config
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig

logger = logging.getLogger(__name__)


def get_drc() -> ZGWClient:
    config = ObjectsAPIConfig.get_solo()
    return config.drc_service.build_client()


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


@register("objects_api")
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
        config.apply_defaults_to(options)

        objects_client = config.objects_service.build_client()

        options["auteur"] = options.get("auteur", "Aanvrager")

        language_code_2b = to_iso639_2b(submission.language_code)

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
            submission.form.admin_name,
            submission_report,
            submission_report_options,
            get_drc=get_drc,
        )

        # TODO turn attachments into dictionary when giving users more options then just urls.
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
                submission.form.admin_name,
                attachment,
                attachment_options,
                get_drc=get_drc,
            )
            attachments.append(attachment_document["url"])

        csv_url = ""
        if (
            options.get("upload_submission_csv", False)
            and options["informatieobjecttype_submission_csv"]
        ):
            submission_csv_options = build_options(
                options,
                {
                    "informatieobjecttype": "informatieobjecttype_submission_csv",
                    "organisatie_rsin": "organisatie_rsin",
                    "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                    "auteur": "auteur",
                },
            )
            submission_csv = create_submission_export(
                Submission.objects.filter(pk=submission.pk).select_related("auth_info")
            ).export("csv")

            submission_csv_document = create_csv_document(
                f"{submission.form.admin_name} (csv)",
                submission_csv,
                submission_csv_options,
                get_drc=get_drc,
                language=language_code_2b,
            )
            csv_url = submission_csv_document["url"]

        base_render_context = {
            "_submission": submission,
            **get_variables_for_context(submission),
            "productaanvraag_type": str(options["productaanvraag_type"]),
            # nested for namespacing note: other templates and context expose all submission
            # variables in the top level namespace, but that is due for refactor
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
                "attachments": attachments,
                "pdf_url": document["url"],
                "csv_url": csv_url,
            },
        }

        template = (
            options.get("content_json") or ObjectsAPIConfig.get_solo().content_json
        )

        record_data = render_from_string(
            template,
            context={**base_render_context},
            disable_autoescape=False,
            backend=openforms_backend,
        )

        if sys.getsizeof(record_data) > settings.OBJECTS_API_DATA_SIZE_LIMIT:
            logger.error(
                "Content JSON field exceeded size of %s with total size: %s",
                settings.OBJECTS_API_DATA_SIZE_LIMIT,
                sys.getsizeof(record_data),
            )
            raise SuspiciousOperation(
                _(
                    "Content JSON field exceeded size of %(max)s with total size: %(total)s.",
                )
                % {
                    "max": settings.OBJECTS_API_DATA_SIZE_LIMIT,
                    "total": sys.getsizeof(record_data),
                }
            )

        try:
            record_data = json.loads(record_data)
        except (TypeError, json.decoder.JSONDecodeError) as err:
            logger.error(
                "Template object doesn't have valid JSON format",
                exc_info=err,
            )
            raise ValidationError(_("Invalid JSON"), code="invalid") from err

        if submission.is_authenticated:
            record_data[submission.auth_info.attribute] = submission.auth_info.value

        object_data = {
            "type": options["objecttype"],
            "record": {
                "typeVersion": options["objecttype_version"],
                "data": record_data,
                "startAt": date.today().isoformat(),
            },
        }
        apply_data_mapping(
            submission, self.object_mapping, REGISTRATION_ATTRIBUTE, object_data
        )

        created_object = objects_client.create("object", object_data)
        return created_object

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
        return [
            "openforms.registrations.contrib.objects_api.templatetags.registrations.contrib.objects_api.json_summary"
        ]
