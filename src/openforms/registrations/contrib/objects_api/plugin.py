from datetime import date
from typing import Optional

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
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
                    },
                    "startAt": date.today().isoformat(),
                },
            },
        )
        return created_object
