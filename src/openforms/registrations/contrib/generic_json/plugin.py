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

from openforms.formio.service import FormioData
from openforms.formio.typing import (
    Component,
    EditGridComponent,
    FileComponent,
)
from openforms.forms.json_schema import NestedDict, generate_json_schema
from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission, SubmissionFileAttachment
from openforms.typing import JSONObject, VariableValue
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import GenericJSONOptionsSerializer
from .constants import PLUGIN_IDENTIFIER
from .registration_variables import register as variables_registry
from .typing import GenericJSONOptions


@register(PLUGIN_IDENTIFIER)
class GenericJSONRegistration(BasePlugin):
    verbose_name = _("Generic JSON registration")
    configuration_options = GenericJSONOptionsSerializer

    # TODO: add GenericJSONResult typed dict to properly indicate return value
    def register_submission(
        self, submission: Submission, options: GenericJSONOptions
    ) -> dict:
        state = submission.load_submission_value_variables_state()

        all_values = state.get_data(include_static_variables=True)
        all_values.update(state.get_static_data(other_registry=variables_registry))

        # Values
        variables = [key for key in options["variables"] if key in all_values]
        values = FormioData({key: all_values[key] for key in variables})
        values_schema = generate_json_schema(
            submission.form,
            variables,
            backend_id=PLUGIN_IDENTIFIER,
            backend_options=options,  # pyright: ignore[reportArgumentType]
            submission=submission,
        )
        transform_to_list = options["transform_to_list"]
        post_process(
            variables, values, NestedDict(values_schema), submission, transform_to_list
        )

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
            backend_id=PLUGIN_IDENTIFIER,
            backend_options=options,  # pyright: ignore[reportArgumentType]
            additional_variables_registry=variables_registry,
        )

        # Send to the service
        data = json.dumps(
            {
                "values": values.data,
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

    @staticmethod
    def allows_json_schema_generation(options: GenericJSONOptions) -> bool:
        return True

    def process_variable_schema(
        self,
        component: Component,
        schema: JSONObject,
        options: GenericJSONOptions,
    ):
        """Process a variable schema for the Generic JSON format.

        The following components need extra attention:
        - File components: we send the content of the file encoded with base64, instead of
          the output from the serializer.
        - Selectboxes components: the selected options could be transformed to a list.
        - Edit grid components: layout component with other components as children, which
          (potentially) need to be processed.

        :param component: Component
        :param schema: JSON schema.
        :param backend_options: Backend options, needed for the transform-to-list option of
          selectboxes components.
        """
        transform_to_list = options["transform_to_list"]

        match component:
            case {"type": "file", "multiple": True}:
                # If multiple is true, the value will be an empty list if no attachments are
                # uploaded, or a list of objects with file name and content as properties
                # when one or more attachments are uploaded
                schema["items"] = {
                    "type": "object",
                    "properties": {
                        "file_name": {"type": "string"},
                        "content": {"type": "string", "format": "base64"},
                    },
                    "required": ["file_name", "content"],
                    "additionalProperties": False,
                }

            case {"type": "file"}:
                # If multiple is false, the value will be None if no attachment is uploaded,
                # or an object with file name and content as properties when one attachment
                # is uploaded
                del schema["items"]
                new_schema = {
                    "type": ["null", "object"],
                    "properties": {
                        "file_name": {"type": "string"},
                        "content": {"type": "string", "format": "base64"},
                    },
                    "required": ["file_name", "content"],
                    "additionalProperties": False,
                }
                schema.update(new_schema)

            case {"type": "selectboxes"} if component["key"] in transform_to_list:
                assert isinstance(schema["properties"], dict)

                # If the component is transformed to a list, we need to adjust the schema
                # accordingly
                schema["type"] = "array"
                schema["items"] = {"type": "string", "enum": list(schema["properties"])}

                for prop in ("properties", "required", "additionalProperties"):
                    schema.pop(prop)

            case {"type": "editgrid"}:
                assert isinstance(schema["items"], dict)
                _properties = schema["items"]["properties"]
                assert isinstance(_properties, dict)

                component = cast(EditGridComponent, component)
                for child_component in component["components"]:
                    child_key = child_component["key"]
                    child_schema = _properties[child_key]
                    assert isinstance(child_schema, dict)
                    self.process_variable_schema(
                        child_component,
                        child_schema,
                        options,
                    )

            case _:
                pass


def post_process(
    variables: list[str],
    values: FormioData,
    schema: NestedDict,
    submission: Submission,
    transform_to_list: list[str] | None = None,
) -> None:
    """Post-process the values and schema.

    - Update the configuration wrapper. This is necessary to update the options for
    Select, SelectBoxes, and Radio components that get their options from another form
    variable.
    - Get all attachments of this submission, and group them by the data path
    - Process each component

    :param variables: List of variable keys to process.
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

    for key in variables:
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
    values: FormioData,
    schema: NestedDict,
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
    schema_key = f"properties.{key.replace('.', '.properties.')}"

    match component:
        case {"type": "file", "multiple": True}:
            values[key] = get_attachments(
                cast(FileComponent, component), attachments, key_prefix
            )

        case {"type": "file"}:  # multiple is False or missing
            attachment_list = get_attachments(
                cast(FileComponent, component), attachments, key_prefix
            )

            variable_schema = schema[schema_key]
            assert isinstance(variable_schema, dict)

            assert (n_attachments := len(attachment_list)) <= 1  # sanity check
            if n_attachments == 0:
                values[key] = None

                variable_schema["type"] = "null"
                for key_to_remove in ("properties", "required", "additionalProperties"):
                    variable_schema.pop(key_to_remove)
            else:
                values[key] = attachment_list[0]
                variable_schema["type"] = "object"

        case {"type": "selectboxes"} if key in transform_to_list:
            values[key] = [
                option
                for option, is_selected in values[key].items()  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]
                if is_selected
            ]

        case {"type": "editgrid"}:
            # Note: the schema actually only needs to be processed once for each child
            # component, but will be processed for each submitted repeating group entry
            # for implementation simplicity.
            edit_grid_schema = NestedDict(schema[schema_key]["items"])  # type: ignore

            component = cast(EditGridComponent, component)

            edit_grid_values_list = cast(list[dict[str, VariableValue]], values[key])
            for index, edit_grid_values in enumerate(edit_grid_values_list):
                edit_grid_values = FormioData(edit_grid_values)

                for child_component in component["components"]:
                    child_key = child_component["key"]

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

                # Need to manually set it to the list, as ``FormioData`` creates a copy
                # so mutations are not applied to ``values``
                edit_grid_values_list[index] = edit_grid_values.data

        case {"type": "partners"}:
            partners = values[key]
            assert isinstance(partners, list)

            for partner in partners:
                assert isinstance(partner, dict)

                # these are not relevant (at least for now)
                partner.pop("firstNames", None)
                partner.pop("dateOfBirthPrecision", None)
                partner.pop("__addedManually", None)

        case _:
            pass


def get_attachments(
    component: FileComponent,
    attachments: dict[str, list[SubmissionFileAttachment]],
    key_prefix: str = "",
) -> list[JSONObject]:
    """Return list of encoded attachments.

    :param component: FileComponent
    :param attachments: Mapping from component submission data path to list of
      attachments corresponding to that component.
    :param key_prefix: If the file component is part of an edit grid component, this key
      prefix includes the parent key and the index of the component as it appears in the
      submitted data list of the edit grid component.

    :return encoded_attachments: List of encoded attachments for this file component.
    """
    key = f"{key_prefix}.{component['key']}" if key_prefix else component["key"]

    return [
        {
            "file_name": attachment.original_name,
            "content": encode_attachment(attachment),
        }
        for attachment in attachments.get(key, [])
    ]


def encode_attachment(attachment: SubmissionFileAttachment) -> str:
    """Encode an attachment using base64.

    :param attachment: Attachment to encode.

    :returns: Encoded base64 data as a string.
    """
    with attachment.content.open("rb") as f:
        f.seek(0)
        return base64.b64encode(f.read()).decode()
