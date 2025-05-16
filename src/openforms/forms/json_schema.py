from __future__ import annotations

import uuid
from collections import UserDict
from typing import Iterator, Sequence, cast

from openforms.formio.service import (
    FormioConfigurationWrapper,
    rewrite_formio_components,
)
from openforms.formio.typing import Component, EditGridComponent, SelectBoxesComponent
from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, JSONValue
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables

from ..registrations.contrib.objects_api.typing import RegistrationOptionsV2
from .models import Form, FormVariable


def _iter_form_variables(
    form: Form,
    additional_variables_registry: BaseRegistry[BaseStaticVariable] | None = None,
) -> Iterator[FormVariable]:
    """Iterate over static variables and all form variables.

    :param form: Form
    :param additional_variables_registry: Optional registry of static variables.
    """
    # Static variables are always available
    yield from get_static_variables()
    # If the optional variables registry is passed
    if additional_variables_registry is not None:
        yield from get_static_variables(
            variables_registry=additional_variables_registry
        )
    # Handle form variables holding dynamic data (component and user defined)
    yield from form.formvariable_set.all()


def generate_json_schema(
    form: Form,
    limit_to_variables: Sequence[str],
    # TODO-5312: this should be the plugin key to enable fetching backend options
    plugin_id: str,
    # TODO-5312: this can be removed and fetched inside this function from the form
    plugin_options: dict,
    additional_variables_registry: BaseRegistry[BaseStaticVariable] | None = None,
    submission: Submission | None = None,
) -> JSONObject:
    """Generate a JSON schema from a form, for the specified variables.

    Note: this schema is an informative description of the variables and should not be
    used as validation.

    :param form: The form to generate JSON schema for.
    :param limit_to_variables: Variables that will be included in the schema.
    :param additional_variables_registry: Optional extra registry of static variables.
    :param submission: Optional submission to use for dynamic data. If not provided, a
      fake submission will be created.

    :returns: A JSON schema representing the form variables.
    """
    if submission is None:
        # Note: we generate a 'fake' submission here to get the total component
        # configuration
        submission = Submission(id=uuid.uuid4(), form=form)

    # Update the total configuration to add options to components that (possibly) use
    # another variable as a data source (radio, select, and selectboxes).
    state = submission.load_submission_value_variables_state()
    new_configuration = rewrite_formio_components(
        submission.total_configuration_wrapper, submission, state.to_python()
    )

    requested_variables_schema = NestedDict()
    for variable in _iter_form_variables(form, additional_variables_registry):
        if variable.key not in limit_to_variables:
            continue

        # Add the new total configuration to the form definition of the variable. Note
        # that we are muting the instance without persisting to the database.
        if variable.source == FormVariableSources.component:
            variable.form_definition.configuration = new_configuration.configuration

        schema = generate_variable_schema(
            variable,
            plugin_id,
            plugin_options,
            submission.total_configuration_wrapper,
        )

        # TODO-5312: this might actually no be necessary for the objects api, as the
        #  values of variables are mapped directly
        process_variable_schema_and_add_to_schema(
            variable.key,
            schema,
            requested_variables_schema,
            submission.total_configuration_wrapper,
        )

    # Result
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": requested_variables_schema.data,
        "required": list(requested_variables_schema),
        "additionalProperties": False,
    }

    return schema


def process_variable_schema_and_add_to_schema(
    key: str,
    variable_schema: JSONObject,
    total_schema: NestedDict,
    configuration_wrapper: FormioConfigurationWrapper,
) -> None:
    """Process the variable schema and add it to the total schema.

    If a variable key contains one or more periods, it will be present in the
    submission data as a nested object, so we need to process the schema to ensure it
    reflects this structure.

    Also, editgrid components need to be processed recursively.

    :param key: The variable key.
    :param variable_schema: The variable schema.
    :param total_schema: The total schema. We use a NestedDict instance for easy nested
      data access through the use of keys with periods.
    :param configuration_wrapper: Updated total configuration wrapper. This is used to
      determine the component type.
    """

    if (
        key in configuration_wrapper
        and configuration_wrapper[key]["type"] == "editgrid"
    ):
        edit_grid_schema = NestedDict()
        for child_key, child_schema in variable_schema["items"]["properties"].items():
            process_variable_schema_and_add_to_schema(
                child_key,
                child_schema,
                edit_grid_schema,
                configuration_wrapper,
            )
        variable_schema["items"]["properties"] = edit_grid_schema.data
        variable_schema["items"]["required"] = list(edit_grid_schema)

    if "." not in key:
        total_schema[key] = variable_schema
        return

    # Replace the periods with a nested 'properties' key
    new_key = key.replace(".", ".properties.")
    total_schema[new_key] = variable_schema

    # Add 'type', 'required', and 'additionalProperty' keywords to the schema for each
    # of the nested levels
    key_list = key.split(".")
    for i in range(1, len(key_list)):
        base = ".properties.".join(key_list[:i])
        total_schema[f"{base}.type"] = "object"
        total_schema[f"{base}.additionalProperties"] = False
        # The 'required' property might already be present from other variables
        required = total_schema.get(f"{base}.required", [])
        required.append(key_list[i])
        total_schema[f"{base}.required"] = required


class NestedDict(UserDict):
    """Data structure to enable nested data access of dictionaries through the use of
    keys with period(s).
    """

    data: dict[str, JSONValue]

    def __getitem__(self, key: str) -> JSONValue:
        """Get a value from the internal dictionary. Keys are expected to be strings,
        and can contain periods to indicate a nested structure.
        """
        value = self.data
        for k in key.split("."):
            value = value[k]
        return value

    def __setitem__(self, key: str, value: JSONValue):
        """Set a value to the internal dictionary. Keys are expected to be strings, and
        can contain periods to indicate a nested structure.
        """
        data = self.data
        key_list = key.split(".")
        for k in key_list[:-1]:
            child = data.get(k, None)
            if child is None:
                data[k] = {}
            data = data[k]
        data[key_list[-1]] = value

    def __contains__(self, key: str) -> bool:
        """Check if a key is present in the internal dictionary. Gets called via
        ``NestedData().get(...)``.
        """
        try:
            self[key]
        except KeyError:
            return False
        return True


def generate_variable_schema(
    variable: FormVariable,
    # TODO-5312: find better name
    plugin_id: str,
    plugin_options,
    configuration_wrapper,
) -> JSONObject:
    """ """
    schema = variable.as_json_schema()

    if variable.source != FormVariableSources.component:
        return schema

    component = configuration_wrapper[variable.key]
    assert component is not None

    if plugin_id == "objects_api":
        process_component_schema_objects_api(
            component, schema, configuration_wrapper, plugin_options
        )
    else:
        raise NotImplementedError()

    return schema


# TODO-5314: better to place this in the registrations.contrib.objects_api to keep
#  everything plugin-related contained?
def process_component_schema_objects_api(
    component: Component,
    schema: JSONObject,
    configuration_wrapper,
    plugin_options: RegistrationOptionsV2,
):
    """Process a component.

    The following components need extra attention:
    - File components: we send the content of the file encoded with base64, instead of
      the output from the serializer.
    - Selectboxes components: the selected options might need to be transformed to a
      list
    - Edit grid components: layout component with other components as children, which
      (potentially) need to be processed.

    :param component: Component
    :param schema: JSON schema.
    :param configuration_wrapper: Updated total configuration wrapper. This is required
      for edit grid components, which need to fetch their children from it.
    :param plugin_options: Plugin options
    """
    key = component["key"]

    match component:
        case {"type": "addressNL"}:
            mapping = plugin_options["variables_mapping"]
            map_ = {}
            for map_ in mapping:
                if map_["variable_key"] == key:
                    break
                return

            if not map_.get("options"):
                return

            # TODO-5312: do processing. This might only be possible if the schema we
            #  pass is the total schema instead of the component schema. This is because
            #  the original component key will not be present in the submitted data, so
            #  we need a way of removing it and moving the keys of the child components
            #  one level up

        case {"type": "file", "multiple": True}:
            # If multiple is true, the value can be an empty list if no attachments are
            # uploaded, and a list of urls when one or more attachments are uploaded
            validate = component.get("validate", {})
            schema["items"] = {"type": "string", "format": "uri"}
            # TODO-5312: this can be moved to the component maybe? Also other components
            #  can have this. For example, a required textfield can have a pattern
            #  matching with one or more characters?
            schema["minItems"] = int(validate.get("required", False))

        case {"type": "file"}:  # multiple is False or missing
            # If multiple is false, the value can be an empty string if no attachment is
            # uploaded, and a single url if one attachment is uploaded
            validate = component.get("validate", {})
            schema["type"] = "string"
            if validate.get("required", False):
                schema["format"] = "uri"
            else:
                schema["oneOf"] = [{"format": "uri"}, {"pattern": "^$"}]
            schema.pop("items")

        case {"type": "selectboxes"} if key in plugin_options["transform_to_list"]:
            component = cast(SelectBoxesComponent, component)
            validate = component.get("validate", {})
            for key_to_remove in ("properties", "required", "additionalProperties"):
                schema.pop(key_to_remove)
            schema["type"] = "array"
            schema["items"] = {
                "type": "string",
                "enum": [options["value"] for options in component["values"]],
            }
            schema["minItems"] = int(validate.get("required", False))

        case {"type": "editgrid"}:
            component = cast(EditGridComponent, component)
            for child_component in component["components"]:
                child_key = child_component["key"]
                # Note that we can't pass the child component directly, as it is not
                # updated during rewriting of formio components
                # TODO-5312: perhaps we can actually, because a selectboxes component
                #  in an edit grid will never be processed, as it cannot be selected
                #  to be transformed to a list
                process_component_schema_objects_api(
                    component=configuration_wrapper[child_key],
                    schema=schema["items"]["properties"][child_key],
                    configuration_wrapper=configuration_wrapper,
                    plugin_options=plugin_options,
                )

        case _:
            pass


"""
Generic JSON schema:
 - file:
    * `None` when there are no uploads and multiple=False
    * An object with file name and content encoded using base64 when there is one upload for multiple=False
    * A list with an empty object when there are no uploads and multiple=True
    * A list of objects with file name and content encoded using base64 for multiple=True
 - selectboxes:
    * Empty dict when it was hidden (is this true? See TODO in code)
    * Processed when transformed to a list. Can we get this setting when generating a
      schema? Or do we need to do an oneOf/anyOf?
"""
