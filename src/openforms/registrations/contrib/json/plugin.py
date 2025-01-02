import base64

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from requests import RequestException
from zgw_consumers.client import build_client

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import JSONOptions, JSONOptionsSerializer
from .models import JSONConfig


@register("json")
class JSONRegistration(BasePlugin):
    verbose_name = _("JSON registration")
    configuration_options = JSONOptionsSerializer

    def register_submission(self, submission: Submission, options: JSONOptions) -> dict:
        values = {}
        # Encode (base64) and add attachments to values dict if their form keys were specified in the
        # form variables list
        for attachment in submission.attachments:
            if attachment.form_key not in options["form_variables"]:
                continue
            options["form_variables"].remove(attachment.form_key)
            with attachment.content.open("rb") as f:
                f.seek(0)
                values[attachment.form_key] = base64.b64encode(f.read()).decode()

        # Create static variables dict
        static_variables = get_static_variables(submission=submission)
        static_variables_dict = {
            variable.key: variable.initial_value for variable in static_variables
        }

        # Update values dict with relevant form data
        all_variables = {**submission.data, **static_variables_dict}
        values.update(
            {
                form_variable: all_variables[form_variable]
                for form_variable in options["form_variables"]
            }
        )

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
                headers={"Content-Type": "application/json"},
            )
            res.raise_for_status()

        return result

    def check_config(self) -> None:
        # Get service
        config = JSONConfig.get_solo()
        if (service := config.service) is None:
            raise InvalidPluginConfiguration(_("Please configure a service"))

        # Check connection to service
        with build_client(service) as client:
            try:
                res = client.get(service.api_connection_check_path)
                res.raise_for_status()
            except RequestException as exc:
                raise InvalidPluginConfiguration(_(f"Invalid response: {exc}")) from exc

    def get_config_actions(self) -> list[tuple[str, str]]:
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:registrations_json_jsonconfig_change",
                    args=(JSONConfig.singleton_instance_id,),
                ),
            )
        ]
