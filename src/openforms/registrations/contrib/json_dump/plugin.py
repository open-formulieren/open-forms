import base64
import json

from django.core.exceptions import SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.formio.typing import Component
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionValueVariable,
)
from openforms.typing import JSONObject
from openforms.variables.constants import FormVariableSources

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
            if key in options["variables"]
        }

        # Process attachments
        self.process_variables(submission, values)

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
        data = json.dumps({"values": values, "schema": schema}, cls=DjangoJSONEncoder)
        service = options["service"]
        submission.registration_result = result = {}
        with build_client(service) as client:
            if ".." in (path := options["path"]):
                raise SuspiciousOperation("Possible path traversal detected")

            res = client.post(path, json=data)
            res.raise_for_status()

            result["api_response"] = res.json()

        return result

    def check_config(self) -> None:
        # Config checks are not really relevant for this plugin right now
        pass

    @staticmethod
    def process_variables(submission: Submission, values: JSONObject):
        """Process variables.

        File components need special treatment, as we send the content of the file
        encoded with base64, instead of the output from the serializer.
        """
        state = submission.load_submission_value_variables_state()

        for key in values.keys():
            variable = state.variables.get(key)
            if (
                variable is None
                or variable.form_variable.source == FormVariableSources.user_defined
            ):
                # None for static variables, and processing user defined variables is
                # not relevant here
                continue

            component = get_component(variable)
            if component is None or component["type"] != "file":
                continue

            encoded_attachments = [
                {
                    "file_name": attachment.original_name,
                    "content": encode_attachment(attachment),
                }
                for attachment in submission.attachments
                if attachment.form_key == key
            ]

            match (
                multiple := component.get("multiple", False),
                n_attachments := len(encoded_attachments)
            ):
                case False, 0:
                    values[key] = None
                case False, 1:
                    values[key] = encoded_attachments[0]
                case True, _:
                    values[key] = encoded_attachments
                case _:
                    raise ValueError(
                        f"Combination of multiple ({multiple}) and number of "
                        f"attachments ({n_attachments}) is not allowed."
                    )


def encode_attachment(attachment: SubmissionFileAttachment) -> str:
    """Encode an attachment using base64

    :param attachment: Attachment to encode
    :returns: Encoded base64 data as a string
    """
    with attachment.content.open("rb") as f:
        f.seek(0)
        return base64.b64encode(f.read()).decode()


def get_component(variable: SubmissionValueVariable) -> Component:
    """Get the component from a submission value variable.

    :param variable: SubmissionValueVariable
    :return component: Component
    """
    config_wrapper = variable.form_variable.form_definition.configuration_wrapper
    component = config_wrapper.component_map[variable.key]

    return component
