import logging

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import Path, glom

from openforms.contrib.objects_api.checks import check_config
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.forms.models import FormVariable
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.submissions.models import Submission
from openforms.typing import JSONObject

from ...base import BasePlugin
from ...registry import register
from ...utils import find_in_dicts

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "objects_api"


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIPrefill(BasePlugin):
    verbose_name = _("Objects API")

    @classmethod
    def get_prefill_values_from_mappings(
        cls,
        submission: Submission,
        form_variable: FormVariable,
    ) -> dict[str, str]:
        variables_mappings = form_variable.prefill_options.get("variables_mapping")
        config_group_id = form_variable.prefill_options.get("objects_api_group")
        config_group = ObjectsAPIGroupConfig.objects.get(id=config_group_id)

        with get_objects_client(config_group) as client:
            obj = client.get_object(submission.initial_data_reference)

        obj_record = obj.get("record", {})
        obj_record_data = glom(obj, "record.data")

        results = {}
        for mapping in variables_mappings:
            path = Path(*mapping["target_path"])
            if value := find_in_dicts(obj_record, obj_record_data, path=path):
                results[mapping["variable_key"]] = value

        return results

    def check_config(self):
        check_config()

    def get_config_actions(self):
        return [
            (
                _("Manage API groups"),
                reverse(
                    "admin:registrations_objects_api_objectsapigroupconfig_changelist"
                ),
            ),
            (
                _("Defaults configuration"),
                reverse(
                    "admin:registrations_objects_api_objectsapiconfig_change",
                    args=(ObjectsAPIConfig.singleton_instance_id,),
                ),
            ),
        ]

    @classmethod
    def configuration_context(cls) -> JSONObject | None:
        return {
            "api_groups": [
                [group.pk, group.name]
                for group in ObjectsAPIGroupConfig.objects.iterator()
            ]
        }
