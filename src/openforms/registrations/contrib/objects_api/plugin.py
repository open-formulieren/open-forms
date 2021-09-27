from copy import deepcopy
from datetime import date
from typing import Any, Dict, NoReturn

from django.utils.translation import ugettext_lazy as _

from zgw_consumers.models import Service

# "Borrow" the functions from another plugin.
from openforms.registrations.contrib.zgw_apis.service import (
    create_attachment,
    create_document,
)
from openforms.submissions.models import Submission, SubmissionReport

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference
from ...registry import register
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig


def get_drc() -> Service:
    config = ObjectsAPIConfig.get_solo()
    return config.drc_service


@register("objects_api")
class ObjectsAPIRegistration(BasePlugin):
    verbose_name = _("Objects API registration")
    configuration_options = ObjectsAPIOptionsSerializer

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
        document = create_document(
            submission.form.admin_name,
            submission_report,
            submission_report_options,
            get_drc=get_drc,
        )

        attachment_options = deepcopy(options)
        attachment_options["informatieobjecttype"] = options[
            "informatieobjecttype_attachment"
        ]
        attachments = []
        for attachment in submission.attachments:
            attachment_document = create_attachment(
                submission.form.admin_name,
                attachment,
                attachment_options,
                get_drc=get_drc,
            )
            attachments.append(attachment_document["url"])

        objects_client = config.objects_service.build_client()

        created_object = objects_client.create(
            "object",
            {
                "type": options["objecttype"],
                "record": {
                    "typeVersion": options["objecttype_version"],
                    "data": {
                        "data": submission.get_merged_data(),
                        "type": options["productaanvraag_type"],
                        "submission_id": str(submission.uuid),
                        "attachments": attachments,
                        "pdf_url": document["url"],
                    },
                    "startAt": date.today().isoformat(),
                },
            },
        )
        return created_object

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Object API plugin does not emit a reference")

    def test_config(self) -> None:
        print("test plugin")
