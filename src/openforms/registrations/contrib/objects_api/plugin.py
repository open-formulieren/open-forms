from copy import deepcopy
from datetime import date
from typing import Any, Dict, NoReturn

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from zgw_consumers.models import Service

from openforms.plugins.exceptions import InvalidPluginConfiguration

# "Borrow" the functions from another plugin.
from openforms.registrations.contrib.zgw_apis.service import (
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport

from ...base import BasePlugin
from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from ...exceptions import NoSubmissionReference
from ...registry import register
from .checks import check_config
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig


def get_drc() -> Service:
    config = ObjectsAPIConfig.get_solo()
    return config.drc_service


def _point_coordinate(value):
    if not value or not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"type": "Point", "coordinates": [value[0], value[1]]}


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
        config = ObjectsAPIConfig.get_solo()
        config.apply_defaults_to(options)

        submission_report = SubmissionReport.objects.get(submission=submission)
        submission_report_options = deepcopy(options)
        submission_report_options["informatieobjecttype"] = options[
            "informatieobjecttype_submission_report"
        ]
        document = create_report_document(
            submission.form.admin_name,
            submission_report,
            submission_report_options,
            get_drc=get_drc,
        )

        attachments = []
        for attachment in submission.attachments:
            attachment_options = deepcopy(options)

            informatieobjecttype = options["informatieobjecttype_attachment"]

            # Use specific IOType if defined
            for attachment_iotype in options.get(
                "informatieobjecttypes_attachments", []
            ):
                if attachment_iotype["attachment_field_name"] == attachment.form_key:
                    informatieobjecttype = attachment_iotype["informatieobjecttype_url"]

            attachment_options["informatieobjecttype"] = informatieobjecttype
            attachment_document = create_attachment_document(
                submission.form.admin_name,
                attachment,
                attachment_options,
                get_drc=get_drc,
            )
            attachments.append(attachment_document["url"])

        objects_client = config.objects_service.build_client()

        object_data = {
            "data": submission.get_merged_data(),
            "type": options["productaanvraag_type"],
            "submission_id": str(submission.uuid),
            "attachments": attachments,
            "pdf_url": document["url"],
        }

        if (
            options.get("upload_submission_csv", False)
            and options["informatieobjecttype_submission_csv"]
        ):
            submission_csv_options = deepcopy(options)
            submission_csv_options["informatieobjecttype"] = options[
                "informatieobjecttype_submission_csv"
            ]
            submission_csv = create_submission_export(
                Submission.objects.filter(pk=submission.pk)
            ).export("csv")

            submission_csv_document = create_csv_document(
                f"{submission.form.admin_name} (csv)",
                submission_csv,
                submission_csv_options,
                get_drc=get_drc,
            )
            object_data["csv_url"] = submission_csv_document["url"]

        if submission.bsn:
            object_data["bsn"] = submission.bsn

        if submission.kvk:
            object_data["kvk"] = submission.kvk

        object_data = {
            "type": options["objecttype"],
            "record": {
                "typeVersion": options["objecttype_version"],
                "data": object_data,
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
