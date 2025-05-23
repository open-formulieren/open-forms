import base64
import json
from collections import defaultdict
from typing import cast

from django.core.exceptions import SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, TextField, Value
from django.db.models.functions import Coalesce, NullIf
from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.formio.typing import (
    Component,
    FileComponent,
    SelectBoxesComponent,
)
from openforms.forms.json_schema import generate_json_schema
from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission, SubmissionFileAttachment
from openforms.typing import JSONObject
from openforms.utils.json_schema import to_multiple
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import GenericJSONOptions, GenericJSONOptionsSerializer
from .registration_variables import register as variables_registry


@register("json_dump")
class GenericJSONRegistration(BasePlugin):
    verbose_name = _("Generic JSON registration")
    configuration_options = GenericJSONOptionsSerializer

    # TODO: add GenericJSONResult typed dict to properly indicate return value
    def register_submission(
        self, submission: Submission, options: GenericJSONOptions
    ) -> dict:
        state = submission.load_submission_value_variables_state()

        # TODO: keys with a period (e.g. `foo.bar`) will currently not be added to the
        #  submission data. This will be fixed with issue 5041
        # Get static values
        static_values = state.get_static_data()
        # Update static values with registration variables
        static_values.update(state.get_static_data(other_registry=variables_registry))

        all_values = state.get_data()
        all_values.update(static_values)

        # Values
        values = {
            key: value
            for key, value in all_values.items()
            if key in options["variables"]
        }
        values_schema = generate_json_schema(
            submission.form, list(values.keys()), submission=submission
        )
        transform_to_list = options["transform_to_list"]
        post_process(values, values_schema, submission, transform_to_list)

        # Metadata
        # Note: as the metadata contains only static variables no post-processing is
        # required.
        metadata_variables = [
            *options["fixed_metadata_variables"],
            *options["additional_metadata_variables"],
        ]
        metadata = {
            key: value for key, value in all_values.items() if key in metadata_variables
        }
        metadata_schema = generate_json_schema(
            submission.form,
            metadata_variables,
            additional_variables_registry=variables_registry,
        )

        # Send to the service
        data = json.dumps(
            {
                "values": values,
                "values_schema": values_schema,
                "metadata": metadata,
                "metadata_schema": metadata_schema,
            },
            cls=DjangoJSONEncoder,
        )
        service = options["service"]
        with build_client(service) as client:
            if ".." in (path := options["path"]):
                raise SuspiciousOperation("Possible path traversal detected")

            result = client.post(
                path, data=data, headers={"content-type": "application/json"}
            )
            result.raise_for_status()

        result_json = result.json() if result.content else ""

        return {"api_response": result_json}

    def check_config(self) -> None:
        # Config checks are not really relevant for this plugin right now
        pass

    def get_variables(self) -> list[FormVariable]:  # pragma: no cover
        return get_static_variables(variables_registry=variables_registry)


def post_process(
    values: JSONObject,
    schema: JSONObject,
    submission: Submission,
    transform_to_list: list[str] | None = None,
) -> None:
    """Post-process the values and schema.

    - Update the configuration wrapper. This is necessary to update the options for
    Select, SelectBoxes, and Radio components that get their options from another form
    variable.
    - Get all attachments of this submission, and group them by the data path
    - Process each component

    :param values: Mapping from key to value of the data to be sent.
    :param schema: JSON schema describing ``values``.
    :param submission: The corresponding submission instance.
    :param transform_to_list: Component keys in this list will be sent as an array of
      values rather than the default object-shape for selectboxes components.
    """
    if transform_to_list is None:
        transform_to_list = []

    state = submission.load_submission_value_variables_state()
    configuration_wrapper = submission.total_configuration_wrapper

    # Create attachment mapping from key or component data path to attachment list
    attachments = submission.attachments.annotate(
        data_path=Coalesce(
            NullIf(
                F("_component_data_path"),
                Value(""),
            ),
            # fall back to variable/component key if no explicit data path is set
            F("submission_variable__key"),
            output_field=TextField(),
        )
    )
    attachments_dict = defaultdict(list)
    for attachment in attachments:
        key = attachment.data_path  # pyright: ignore[reportAttributeAccessIssue]
        attachments_dict[key].append(attachment)

    for key in values.keys():
        variable = state.variables.get(key)
        if (
            variable is None
            or variable.form_variable is None
            or variable.form_variable.source == FormVariableSources.user_defined
        ):
            # None for static variables, and processing user defined variables is
            # not relevant here
            continue

        component = configuration_wrapper[key]
        assert component is not None

        process_component(
            component,
            values,
            schema,
            attachments_dict,
            configuration_wrapper,
            transform_to_list=transform_to_list,
        )


def process_component(
    component: Component,
    values: JSONObject,
    schema: JSONObject,
    attachments: dict[str, list[SubmissionFileAttachment]],
    configuration_wrapper,
    key_prefix: str = "",
    transform_to_list: list[str] | None = None,
) -> None:
    """Process a component.

    The following components need extra attention:
    - File components: we send the content of the file encoded with base64, instead of
      the output from the serializer.
    - Selectboxes components: the selected options might need to be transformed to a
      list
    - Edit grid components: layout component with other components as children, which
      (potentially) need to be processed.

    :param component: Component
    :param values: Mapping from key to value of the data to be sent.
    :param schema: JSON schema describing ``values``.
    :param attachments: Mapping from component submission data path to list of
      attachments corresponding to that component.
    :param configuration_wrapper: Updated total configuration wrapper. This is required
      for edit grid components, which need to fetch their children from it.
    :param key_prefix: If the component is part of an edit grid component, this key
      prefix includes the parent key and the index of the component as it appears in the
      submitted data list of that edit grid component.
    :param transform_to_list: Component keys in this list will be sent as an array of
      values rather than the default object-shape for selectboxes components.
    """
    if transform_to_list is None:
        transform_to_list = []

    key = component["key"]
    assert isinstance(schema["properties"], dict)

    match component:
        case {"type": "file", "multiple": True}:
            attachment_list, base_schema = get_attachments_and_base_schema(
                cast(FileComponent, component), attachments, key_prefix
            )
            values[key] = attachment_list
            schema["properties"][key] = to_multiple(base_schema)

        case {"type": "file"}:  # multiple is False or missing
            attachment_list, base_schema = get_attachments_and_base_schema(
                cast(FileComponent, component), attachments, key_prefix
            )

            assert (n_attachments := len(attachment_list)) <= 1  # sanity check
            if n_attachments == 0:
                value = None
                base_schema = {"title": component["label"], "type": "null"}
            else:
                value = attachment_list[0]
            values[key] = value
            schema["properties"][key] = base_schema  # pyright: ignore[reportArgumentType]

        case {"type": "selectboxes"}:
            component = cast(SelectBoxesComponent, component)

            # If the select boxes component was hidden, the submitted data of this
            # component is an empty dict, so set the required to an empty list.
            if not values[key]:
                schema["properties"][key]["required"] = []  # type: ignore

            if key not in transform_to_list:
                return

            # Convert the values to a list and update the schema accordingly
            choices = [options["value"] for options in component["values"]]  # type: ignore[reportTypedDictNotRequiredAccess]
            base_schema = {
                "type": "array",
                "items": {"type": "string", "enum": choices},
            }
            _properties = schema["properties"][key]
            assert isinstance(_properties, dict)
            _properties.update(base_schema)

            keys_to_remove = ("properties", "required", "additionalProperties")
            for k in keys_to_remove:
                _properties.pop(k, None)

            values[key] = [
                option
                for option, is_selected in values[key].items()  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]
                if is_selected
            ]

        case {"type": "editgrid"}:
            # Note: the schema actually only needs to be processed once for each child
            # component, but will be processed for each submitted repeating group entry
            # for implementation simplicity.
            edit_grid_schema: JSONObject = schema["properties"][key]["items"]  # type: ignore

            for index, edit_grid_values in enumerate(
                cast(list[JSONObject], values[key])
            ):
                for child_key in edit_grid_values.keys():
                    process_component(
                        component=configuration_wrapper[child_key],
                        values=edit_grid_values,
                        schema=edit_grid_schema,
                        attachments=attachments,
                        configuration_wrapper=configuration_wrapper,
                        key_prefix=(
                            f"{key_prefix}.{key}.{index}"
                            if key_prefix
                            else f"{key}.{index}"
                        ),
                    )

        case _:
            pass


def get_attachments_and_base_schema(
    component: FileComponent,
    attachments: dict[str, list[SubmissionFileAttachment]],
    key_prefix: str = "",
) -> tuple[list[JSONObject], JSONObject]:
    """Return list of encoded attachments and the base schema.

    :param component: FileComponent
    :param attachments: Mapping from component submission data path to list of
      attachments corresponding to that component.
    :param key_prefix: If the file component is part of an edit grid component, this key
      prefix includes the parent key and the index of the component as it appears in the
      submitted data list of the edit grid component.

    :return encoded_attachments: List of encoded attachments for this file component.
    :return base_schema: JSON schema describing the entries of ``encoded_attachments``.
    """
    key = f"{key_prefix}.{component['key']}" if key_prefix else component["key"]

    encoded_attachments: list[JSONObject] = [
        {
            "file_name": attachment.original_name,
            "content": encode_attachment(attachment),
        }
        for attachment in attachments.get(key, [])
    ]

    base_schema: JSONObject = {
        "title": component["label"],
        "type": "object",
        "properties": {
            "file_name": {"type": "string"},
            "content": {"type": "string", "format": "base64"},
        },
        "required": (
            ["file_name", "content"] if len(encoded_attachments) != 0 else []
            # No required properties when there are no attachments
        ),
        "additionalProperties": False,
    }

    return encoded_attachments, base_schema


def encode_attachment(attachment: SubmissionFileAttachment) -> str:
    """Encode an attachment using base64.

    :param attachment: Attachment to encode.

    :returns: Encoded base64 data as a string.
    """
    with attachment.content.open("rb") as f:
        f.seek(0)
        return base64.b64encode(f.read()).decode()
