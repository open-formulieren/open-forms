import base64

from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.submissions.models import Submission
from openforms.typing import JSONObject
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import JSONDumpOptions, JSONDumpOptionsSerializer


@register("json_dump")
class JSONDumpRegistration(BasePlugin):
    verbose_name = _("JSON dump registration")
    configuration_options = JSONDumpOptionsSerializer

    def register_submission(
        self, submission: Submission, options: JSONDumpOptions
    ) -> dict:
        state = submission.load_submission_value_variables_state()

        all_values: JSONObject = {
            **state.get_static_data(),
            **state.get_data(),  # dynamic values from user input
        }
        values = {
            key: value
            for key, value in all_values.items()
            if key in options["form_variables"]
        }

        # Encode (base64) and add attachments to values dict if their form keys were specified in the
        # form variables list
        for attachment in submission.attachments:
            if attachment.form_key not in options["form_variables"]:
                continue
            options["form_variables"].remove(attachment.form_key)
            with attachment.content.open("rb") as f:
                f.seek(0)
                values[attachment.form_key] = base64.b64encode(f.read()).decode()

        # Generate schema
        # TODO: will be added in #4980. Hardcoded example for now.
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "static_var_1": {"type": "string", "pattern": "^cool_pattern$"},
                "form_var_1": {"type": "string"},
                "form_var_2": {"type": "string"},
                "attachment": {"type": "string", "contentEncoding": "base64"},
            },
            "required": ["static_var_1", "form_var_1", "form_var_2"],
            "additionalProperties": False,
        }

        # Send to the service
        json = {"values": values, "schema": schema}
        service = options["service"]
        submission.registration_result = result = {}
        with build_client(service) as client:
            result["api_response"] = res = client.post(
                options.get("relative_api_endpoint", ""),
                json=json,
            )
            res.raise_for_status()

        return result

    def check_config(self) -> None:
        # Config checks are not really relevant for this plugin right now
        pass
