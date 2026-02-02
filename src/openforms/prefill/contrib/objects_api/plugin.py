from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from glom import Path, PathAccessError, glom

from openforms.contrib.objects_api.checks import check_config
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.ownership_validation import validate_object_ownership
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable, JSONObject

from ...base import BasePlugin
from ...registry import register
from .api.serializers import ObjectsAPIOptionsSerializer
from .typing import ObjectsAPIOptions

logger = structlog.stdlib.get_logger(__name__)


PLUGIN_IDENTIFIER = "objects_api"


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIPrefill(BasePlugin[ObjectsAPIOptions]):
    verbose_name = _("Objects API")
    options = ObjectsAPIOptionsSerializer

    def verify_initial_data_ownership(
        self, submission: Submission, prefill_options: ObjectsAPIOptions
    ) -> None:
        if prefill_options["skip_ownership_check"]:
            logger.info(
                "skip_ownership_check",
                submission_uuid=str(submission.uuid),
                plugin=self,
            )
            return

        assert submission.initial_data_reference
        api_group = prefill_options["objects_api_group"]
        assert api_group, "Can't do anything useful without an API group"

        auth_attribute_path = prefill_options["auth_attribute_path"]
        assert auth_attribute_path, "Auth attribute path may not be empty"

        with (
            get_objects_client(api_group) as client,
            structlog.contextvars.bound_contextvars(plugin=self),
        ):
            validate_object_ownership(submission, client, auth_attribute_path)

    @classmethod
    def get_prefill_values_from_options(
        cls,
        submission: Submission,
        options: ObjectsAPIOptions,
        submission_value_variable: SubmissionValueVariable,
    ) -> dict[str, JSONEncodable]:
        with get_objects_client(options["objects_api_group"]) as client:
            obj = client.get_object(submission.initial_data_reference)

        obj_record = obj.get("record", {})
        prefix = "data"

        results = {}
        for mapping in options["variables_mapping"]:
            path = Path(prefix, *mapping["target_path"])

            try:
                value = glom(obj_record, path)
            except PathAccessError:
                continue
            results[mapping["variable_key"]] = value

        return results

    def check_config(self):
        check_config()

    def get_config_actions(self):
        return [
            (
                _("Manage API groups"),
                reverse("admin:objects_api_objectsapigroupconfig_changelist"),
            ),
        ]

    @classmethod
    def configuration_context(cls) -> JSONObject | None:
        return {
            "api_groups": [
                [group.identifier, group.name]
                for group in ObjectsAPIGroupConfig.objects.iterator()
            ]
        }
