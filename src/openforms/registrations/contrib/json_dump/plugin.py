import base64

from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.forms.utils import form_variables_to_json_schema
from openforms.formio.typing import Component
from openforms.submissions.models import Submission, SubmissionValueVariable, \
    SubmissionFileAttachment
from openforms.typing import JSONObject

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

        # Process attachments
        self.process_variables(submission, values)

        # Generate schema
        schema = form_variables_to_json_schema(submission.form, options["form_variables"])

        # TODO-4980: this can be cleaned up probably
        # Change schema of files, as we do some custom processing in this plugin
        attachment_vars = [
            var for var in submission.form.formvariable_set.all()
            if var.key in set(options["form_variables"]).difference(form_vars)
        ]
        for variable in attachment_vars:
            form_def = variable.form_definition
            component = form_def.configuration_wrapper.component_map[variable.key]
            # TODO-4980: enable this when the attachment processing is cleaned up
            # multiple = component.get("multiple", False)
            multiple = False

            base = {"type": "string", "format": "base64"}
            schema["properties"][variable.key] = (
                {"type": "array", "items": base} if multiple else base
            )

        # Send to the service
        json = {"values": values, "schema": schema}
        service = options["service"]
        submission.registration_result = result = {}
        with build_client(service) as client:
            res = client.post(
                options.get("relative_api_endpoint", ""),
                json=json,
            )
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
            if variable is None:
                # None for static variables
                continue

            component = get_component(variable)
            if component is None or component["type"] != "file":
                continue

            encoded_attachments = {
                attachment.file_name: encode_attachment(attachment)
                for attachment in submission.attachments
                if attachment.form_key == key
            }
            multiple = component.get("multiple", False)
            values[key] = (
                encoded_attachments
                if multiple
                else list(encoded_attachments.values())[0]
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
