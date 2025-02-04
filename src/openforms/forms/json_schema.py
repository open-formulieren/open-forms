from typing import Iterator, Sequence

from openforms.plugins.registry import BaseRegistry
from openforms.typing import JSONObject
from openforms.variables.base import BaseStaticVariable
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
    # Handle from variables holding dynamic data (component and user defined)
    yield from form.formvariable_set.all()


def generate_json_schema(
    form: Form,
    limit_to_variables: Sequence[str],
    additional_variables_registry: BaseRegistry[BaseStaticVariable] | None = None,
) -> JSONObject:
    """Generate a JSON schema from a form, for the specified variables.

    Note: this schema is an informative description of the variables and should not be
    used as validation.

    :param form: The form to generate JSON schema for.
    :param limit_to_variables: Variables that will be included in the schema.
    :param additional_variables_registry: Optional extra registry of static variables.

    :returns: A JSON schema representing the form variables.
    """
    requested_variables_schema = {
        key: variable.as_json_schema()
        for variable in _iter_form_variables(form, additional_variables_registry)
        if (key := variable.key) in limit_to_variables
    }

    # TODO: this will be added with issue 4923
    # process this with deep objects etc., the FormioData data structure might be
    # useful here

    # Result
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": requested_variables_schema,
        "required": limit_to_variables,
        "additionalProperties": False,
    }

    return schema
