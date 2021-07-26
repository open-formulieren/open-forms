from datetime import date
from typing import Optional

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission, SubmissionReport

from ...base import BasePlugin
from ...registry import register
from ..zgw_apis.models import ZgwConfig
from ..zgw_apis.service import create_document
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig


@register("objects_api")
class ObjectsAPIRegistration(BasePlugin):
    verbose_name = _("Objects API registration")
    configuration_options = ObjectsAPIOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        config = ObjectsAPIConfig.get_solo()
        config.apply_defaults_to(options)

        zgw_config = ZgwConfig.get_solo()
        zgw_config.apply_defaults_to(options)

        submission_report = SubmissionReport.objects.get(submission=submission)
        document = create_document(submission.form.name, submission_report, options)

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
                        "pdf_url": document["url"],
                    },
                    "startAt": date.today().isoformat(),
                },
            },
        )
        return created_object
