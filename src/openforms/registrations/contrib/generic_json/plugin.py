import base64
from collections import defaultdict
from collections.abc import Mapping
from functools import partial
from typing import cast  # noqa: TID251

from django.core.exceptions import SuspiciousOperation
from django.db.models import F, TextField, Value
from django.db.models.functions import Coalesce, NullIf
from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
)
from openforms.formio.typing import (
    Component,
    EditGridComponent,
    FileComponent,
)
from openforms.forms.json_schema import NestedDict
from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission, SubmissionFileAttachment
from openforms.typing import JSONObject, VariableValue
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...json_output import ComponentPostProcessHook, get_json_data
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
        state = submission.variables_state

        all_values = state.get_data(include_static_variables=True)
        all_values.update(state.get_static_data(other_registry=variables_registry))

        variables = [key for key in options["variables"] if key in all_values]

        # Values
        post_process_component = build_post_process_component_hook(
            submission=submission, transform_to_list=options["transform_to_list"]
        )
        document_data = get_json_data(
            submission,
            values=all_values,
            limit_to_variables=variables,
            backend_id=PLUGIN_IDENTIFIER,
            # the cast is just for the type checker - this can be resolved at
            # some point with union types I suppose
            backend_options=dict(options),
            post_process_component=post_process_component,
        )

        # Metadata
        # Note: as the metadata contains only static variables no post-processing is
        # required.
        metadata_variables = [
            *options["fixed_metadata_variables"],
            *options["additional_metadata_variables"],
        ]
        metadata_json_data = get_json_data(
            submission,
            values=all_values,
            limit_to_variables=metadata_variables,
            backend_id=PLUGIN_IDENTIFIER,
            # the cast is just for the type checker - this can be resolved at
            # some point with union types I suppose
            backend_options=dict(options),
            additional_variables=self.get_variables(),
        )

        # serialize and include the metadata keys, to send it to the service
        data = document_data.serialize(
            metadata=metadata_json_data.values.data,
            metadata_schema=metadata_json_data.values_schema,
        )
        # Send to the service
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
        configuration_wrapper: FormioConfigurationWrapper,
    ):
        """
        Process a variable schema for the Generic JSON format.

        The following components need extra attention:
        - File components: we send the content of the file encoded with base64, instead of
          the output from the serializer.
        - Selectboxes components: the selected options could be transformed to a list.
        - Edit grid components: layout component with other components as children, which
          (potentially) need to be processed.

        :param component: Component
        :param schema: JSON schema.
        :param options: Backend options, needed for the transform-to-list option of
          selectboxes components.
        :param configuration_wrapper: Formio configuration wrapper.
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

                for child_key, child_schema in _properties.items():
                    child_component = configuration_wrapper[child_key]
                    assert isinstance(child_schema, dict)
                    self.process_variable_schema(
                        child_component,
                        child_schema,
                        options,
                        configuration_wrapper,
                    )

            case _:
                pass


def build_post_process_component_hook(
    submission: Submission,
    transform_to_list: list[str] | None = None,
) -> ComponentPostProcessHook:
    """
    Build a callback function for component-specific post-processing.

    :param submission: The corresponding submission instance.
    :param transform_to_list: Component keys in this list will be sent as an array of
      values rather than the default object-shape for selectboxes components.
    """
    if transform_to_list is None:
        transform_to_list = []

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

    post_process_component = partial(
        process_component,
        attachments=attachments_dict,
        configuration_wrapper=submission.total_configuration_wrapper,
        transform_to_list=transform_to_list,
    )
    return post_process_component


def process_component(
    component: Component,
    value: VariableValue,
    schema: NestedDict,
    attachments: dict[str, list[SubmissionFileAttachment]],
    configuration_wrapper,
    key_prefix: str = "",
    transform_to_list: list[str] | None = None,
) -> VariableValue:
    """Process a component.

    The following components need extra attention:
    - File components: we send the content of the file encoded with base64, instead of
      the output from the serializer.
    - Selectboxes components: the selected options might need to be transformed to a
      list
    - Edit grid components: layout component with other components as children, which
      (potentially) need to be processed.

    :param component: Component
    :param value: Current value of the provided component.
    :param schema: JSON schema describing the values of the submission.
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
            _component = cast(FileComponent, component)
            return get_attachments(_component, attachments, key_prefix)

        case {"type": "file"}:  # multiple is False or missing
            _component = cast(FileComponent, component)
            attachment_list = get_attachments(_component, attachments, key_prefix)

            variable_schema = schema[schema_key]
            assert isinstance(variable_schema, dict)

            n_attachments = len(attachment_list)
            assert n_attachments <= 1  # sanity check
            if n_attachments == 0:
                variable_schema["type"] = "null"
                for key_to_remove in ("properties", "required", "additionalProperties"):
                    variable_schema.pop(key_to_remove)
                return None
            else:
                variable_schema["type"] = "object"
                return attachment_list[0]

        case {"type": "selectboxes"} if key in transform_to_list:
            assert isinstance(value, Mapping)
            return [option for option, is_selected in value.items() if is_selected]

        case {"type": "editgrid"}:
            component = cast(EditGridComponent, component)

            # Note: the schema actually only needs to be processed once for each child
            # component, but will be processed for each submitted repeating group entry
            # for implementation simplicity.
            array_schema = schema[schema_key]
            assert isinstance(array_schema, Mapping)
            item_schema = array_schema["items"]
            assert isinstance(item_schema, Mapping)
            edit_grid_schema = NestedDict(item_schema)

            assert isinstance(value, list)
            # recurse into editgrids and apply the post-processing for nested components
            new_value: list[VariableValue] = []
            for index, item_values in enumerate(value):
                assert isinstance(item_values, Mapping)
                _item_values = FormioData(item_values)
                new_item_values = FormioData()
                for child_component in component["components"]:
                    child_key = child_component["key"]
                    child_value = process_component(
                        component=configuration_wrapper[child_key],
                        # keys may be absent if the field is hidden
                        # XXX check if this still applies after the clear on hide rework
                        value=_item_values.get(child_key),
                        schema=edit_grid_schema,
                        attachments=attachments,
                        configuration_wrapper=configuration_wrapper,
                        key_prefix=(
                            f"{key_prefix}.{key}.{index}"
                            if key_prefix
                            else f"{key}.{index}"
                        ),
                    )
                    new_item_values[child_key] = child_value

                # Need to manually set it to the list, as ``FormioData`` creates a copy
                # so mutations are not applied to ``values``
                new_value.append(new_item_values.data)

            return new_value

        case _:
            return value


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
