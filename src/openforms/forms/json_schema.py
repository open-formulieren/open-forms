from typing import Iterator, Sequence

from openforms.typing import JSONObject
from openforms.variables.service import get_static_variables

from .models import Form, FormVariable


def _iter_form_variables(form: Form) -> Iterator[FormVariable]:
    """Iterate over static variables and all form variables.

    :param form: Form
    """
    # Static variables are always available
    yield from get_static_variables()
    # Handle from variables holding dynamic data (component and user defined)
    yield from form.formvariable_set.all()


def generate_json_schema(form: Form, limit_to_variables: Sequence[str]) -> JSONObject:
    """Generate a JSON schema from a form, for the specified variables.

    Note: this schema is an informative description of the variables and should not be
    used as validation.

    :param form: The form to generate JSON schema for.
    :param limit_to_variables: Variables that will be included in the schema.

    :returns: A JSON schema representing the form variables.
    """
    requested_variables_schema = {
        key: variable.as_json_schema()
        for variable in _iter_form_variables(form)
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
