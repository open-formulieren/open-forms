from __future__ import annotations

import uuid
from collections import UserDict
from typing import Iterator, Sequence

from openforms.formio.service import (
    FormioConfigurationWrapper,
    rewrite_formio_components,
)
from openforms.plugins.registry import BaseRegistry
from openforms.registrations.service import process_variable_schema
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, JSONValue
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables

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
    backend_id: str = "",
    backend_options: dict | None = None,
    additional_variables_registry: BaseRegistry[BaseStaticVariable] | None = None,
    submission: Submission | None = None,
) -> JSONObject:
    """Generate a JSON schema from a form, for the specified variables.

    Note: this schema is an informative description of the variables and should not be
    used as validation.

    :param form: The form to generate JSON schema for.
    :param limit_to_variables: Variables that will be included in the schema.
    :param backend_id: Optional registration backend identifier for which to generate
      the schema.
    :param backend_options: Optional registration backend options.
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
            submission.total_configuration_wrapper,
            backend_id,
            backend_options,
        )

        process_variable_schema_and_add_to_complete_schema(
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


def generate_variable_schema(
    variable: FormVariable,
    configuration_wrapper: FormioConfigurationWrapper,
    backend_id: str = "",
    backend_options: dict | None = None,
) -> JSONObject:
    """Generate the schema for a form variable.

    To ensure the schema represents the submission data that is sent through different
    registration backends, we need to perform some processing.

    :param variable: The form variable.
    :param configuration_wrapper: Updated total configuration wrapper. This is used to
      get the component from.
    :param backend_id: The registration backend identifier. If an empty string is
      passed, no processing of the schema is performed, meaning it will represent the
      formio submission data.
    :param backend_options: Optional registration backend options. If ``backend_id`` was
      provided, this cannot be ``None``.

    :return: Schema for the variable.
    """
    schema = variable.as_json_schema()

    if variable.source != FormVariableSources.component:
        return schema

    component = configuration_wrapper[variable.key]
    assert component is not None

    if backend_id:
        assert backend_options is not None
        process_variable_schema(component, schema, backend_id, backend_options)

    return schema


def process_variable_schema_and_add_to_complete_schema(
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
            process_variable_schema_and_add_to_complete_schema(
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
