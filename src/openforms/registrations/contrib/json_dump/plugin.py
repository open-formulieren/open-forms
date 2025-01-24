import base64
import json
from typing import cast

from django.core.exceptions import SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.formio.service import rewrite_formio_components
from openforms.formio.typing import (
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
)
from openforms.forms.utils import form_variables_to_json_schema
from openforms.submissions.models import Submission, SubmissionFileAttachment
from openforms.submissions.service import DataContainer
from openforms.typing import JSONObject
from openforms.utils.json_schema import to_multiple
from openforms.variables.constants import FormVariableSources

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import JSONDumpOptions, JSONDumpOptionsSerializer


@register("json_dump")
class JSONDumpRegistration(BasePlugin):
    verbose_name = _("JSON dump registration")
    configuration_options = JSONDumpOptionsSerializer

    # TODO: add JSONDumpResult typed dict to properly indicate return value
    def register_submission(
        self, submission: Submission, options: JSONDumpOptions
    ) -> dict:
        state = submission.load_submission_value_variables_state()

        # Generate values
        all_values: JSONObject = {
            **state.get_static_data(),
            **state.get_data(),  # dynamic values from user input
        }
        values = {
            key: value
            for key, value in all_values.items()
            if key in options["variables"]
        }

        # Generate schema
        schema = form_variables_to_json_schema(submission.form, options["variables"])

        # Post-processing
        post_process(values, schema, submission)

        # Send to the service
        data = json.dumps({"values": values, "schema": schema}, cls=DjangoJSONEncoder)
        service = options["service"]
        with build_client(service) as client:
            if ".." in (path := options["path"]):
                raise SuspiciousOperation("Possible path traversal detected")

            result = client.post(path, json=data)
            result.raise_for_status()

        return {"api_response": result.json()}

    def check_config(self) -> None:
        # Config checks are not really relevant for this plugin right now
        pass


def post_process(
    values: JSONObject, schema: JSONObject, submission: Submission
) -> None:
    """Post-process the values and schema.

    File components need special treatment, as we send the content of the file
    encoded with base64, instead of the output from the serializer. Also, Radio,
    Select, and SelectBoxes components need to be updated if their data source is
    set to another form variable.

    :param values: JSONObject
    :param schema: JSONObject
    :param submission: Submission
    """
    state = submission.load_submission_value_variables_state()

    # Update config wrapper. This is necessary to update the options for Select,
    # SelectBoxes, and Radio components that get their options from another form
    # variable.
    data = DataContainer(state=state)
    configuration_wrapper = rewrite_formio_components(
        submission.total_configuration_wrapper,
        submission=submission,
        data=data.data,
    )

    for key in values.keys():
        variable = state.variables.get(key)
        if (
            variable is None
            or variable.form_variable.source == FormVariableSources.user_defined
        ):
            # None for static variables, and processing user defined variables is
            # not relevant here
            continue

        component = configuration_wrapper[key]
        assert component is not None

        match component:
            case {"type": "file", "multiple": True}:
                attachment_list, base_schema = get_attachments_and_base_schema(
                    cast(FileComponent, component), submission
                )
                values[key] = attachment_list  # type: ignore
                schema["properties"][key] = to_multiple(base_schema)  # type: ignore

            case {"type": "file"}:  # multiple is False or missing
                attachment_list, base_schema = get_attachments_and_base_schema(
                    cast(FileComponent, component), submission
                )

                assert (n_attachments := len(attachment_list)) <= 1  # sanity check
                if n_attachments == 0:
                    value = None
                    base_schema = {"title": component["label"], "type": "null"}
                else:
                    value = attachment_list[0]
                values[key] = value
                schema["properties"][key] = base_schema  # type: ignore

            case {"type": "radio", "openForms": {"dataSrc": "variable"}}:
                component = cast(RadioComponent, component)
                choices = [options["value"] for options in component["values"]]
                choices.append("")  # Take into account an unfilled field
                schema["properties"][key]["enum"] = choices  # type: ignore

            case {"type": "select", "openForms": {"dataSrc": "variable"}}:
                component = cast(SelectComponent, component)
                choices = [options["value"] for options in component["data"]["values"]]  # type: ignore[reportTypedDictNotRequiredAccess]
                choices.append("")  # Take into account an unfilled field

                if component.get("multiple", False):
                    schema["properties"][key]["items"]["enum"] = choices  # type: ignore
                else:
                    schema["properties"][key]["enum"] = choices  # type: ignore

            case {"type": "selectboxes"}:
                component = cast(SelectBoxesComponent, component)
                data_src = component.get("openForms", {}).get("dataSrc")

                if data_src == "variable":
                    properties = {
                        options["value"]: {"type": "boolean"}
                        for options in component["values"]
                    }
                    base_schema = {
                        "properties": properties,
                        "required": list(properties.keys()),
                        "additionalProperties": False,
                    }
                    schema["properties"][key].update(base_schema)  # type: ignore

                # If the select boxes component was hidden, the submitted data of this
                # component is an empty dict, so set the required to an empty list.
                if not values[key]:
                    schema["properties"][key]["required"] = []  # type: ignore
            case _:
                pass


def get_attachments_and_base_schema(
    component: FileComponent, submission: Submission
) -> tuple[list[JSONObject], JSONObject]:
    """Return list of encoded attachments and the base schema.

    :param component: FileComponent
    :param submission: Submission

    :return encoded_attachments: list[JSONObject]
    :return base_schema: JSONObject
    """
    encoded_attachments: list[JSONObject] = [
        {
            "file_name": attachment.original_name,
            "content": encode_attachment(attachment),
        }
        for attachment in submission.attachments
        if attachment.form_key == component["key"]
    ]

    base_schema: JSONObject = {
        "title": component["label"],
        "type": "object",
        "properties": {
            "file_name": {"type": "string"},
            "content": {"type": "string", "format": "base64"},
        },
        "required": (
            ["file_name", "content"]
            if len(encoded_attachments) != 0
            else []
            # No required properties when there are no attachments
        ),
        "additionalProperties": False,
    }

    return encoded_attachments, base_schema


def encode_attachment(attachment: SubmissionFileAttachment) -> str:
    """Encode an attachment using base64

    :param attachment: Attachment to encode
    :returns: Encoded base64 data as a string
    """
    with attachment.content.open("rb") as f:
        f.seek(0)
        return base64.b64encode(f.read()).decode()
