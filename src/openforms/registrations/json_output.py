"""
Support serializing submission data to a JSON document.

The datastructures and routines in this module serve as building block for the
generic JSON plugin and ZGW APIs plugin that (optionally) produce a JSON document with
the variables and their values of a single submission.

.. todo:: The MS Graph (Sharepoint) registration plugin should also make use of this,
   but we can't just simply change the output format as that's a breaking change.
"""

import json
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Protocol

from django.core.serializers.json import DjangoJSONEncoder

from openforms.formio.datastructures import FormioData
from openforms.formio.service import as_json_data
from openforms.formio.typing import Component
from openforms.forms.json_schema import NestedDict, generate_json_schema
from openforms.forms.models.form_variable import FormVariable
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, VariableValue
from openforms.variables.constants import FormVariableSources

type AnyOptionsDict = dict[str, object]


class ComponentPostProcessHook(Protocol):
    def __call__(
        self,
        component: Component,
        value: VariableValue,
        schema: NestedDict,
    ) -> VariableValue:
        """
        Post process the component (value and schema).

        Each registration backend can provide a post-processing hook which will be
        called for each component and its value, for each component variable that's
        included in the JSON data and schema.

        :param component: The specific component instance to be post processed.
        :param value: The component value. If the Formio component registry for the
          component type implements (registration backend independent) value
          transformations, they have already been applied.
        :param schema: The generated JSON schema, based on the component and variable
          definitions. Registration backend specific changes must be applied as
          mutations.
        :returns: The transformed/modified variable, specific to caller providing the
          post processing hook.
        """
        ...


@dataclass
class JSONDocumentData:
    """
    Container data structure for the json document data of a submission.
    """

    values: FormioData
    """
    Values from the specified form variables to include.
    """
    values_schema: JSONObject
    """
    JSON Schema definition describing the values.

    The schema definition allows generic data-displaying tooling to interpret the
    values and render them in a user-interface.
    """

    def serialize(self, **extra) -> str:
        return json.dumps(
            {
                "values": self.values.data,
                "values_schema": self.values_schema,
                **extra,
            },
            cls=DjangoJSONEncoder,
        )


def get_json_data(
    submission: Submission,
    *,
    values: FormioData,
    limit_to_variables: Sequence[str],
    backend_id: str,
    backend_options: AnyOptionsDict,
    post_process_component: ComponentPostProcessHook | None = None,
    additional_variables: Collection[FormVariable] = (),
) -> JSONDocumentData:
    """
    Extract the submission variables data in a format suitable for JSON documents.

    This is a generic building block intended to be post-processed by specific
    registration backends. Variables belonging to Formio component definitions are
    already processed in a generic way through the formio component registry.

    :param submission: The submission for which the JSON data is being produced.
    :param values: The raw submission data to grab values from.
    :param limit_to_variables: Variable names (keys) to include in the output values
      and schema describing the values.
    :param backend_id: Registration backend identifier requesting the json data. Schema
      generation requires this context for backend-specific post-processing.
    :param backend_options: Registration backend options. Note: there is currently no
      check if the options correspond to the provided ``backend_id``, so please ensure
      that they do.
    :param post_process_component: Optional callback to post-process the value and
      schema of a Formio component variable, allowing for backend-specific value and
      schema modifications.
    :param additional_variables: Optional collection of additional static variables to
      include in the JSON schema generation.
    """
    state = submission.variables_state
    configuration_wrapper = submission.total_configuration_wrapper

    values_schema = generate_json_schema(
        submission.form,
        limit_to_variables=limit_to_variables,
        backend_id=backend_id,
        backend_options=backend_options,
        submission=submission,
        additional_variables=additional_variables,
    )
    schema_for_post_processing = NestedDict(values_schema)

    # filter and process only the requested variables
    output_values = FormioData()
    for key in limit_to_variables:
        variable = state.variables.get(key)
        value = values[key]

        # run component-specific processing for component variables
        if (
            variable
            and variable.form_variable
            and variable.form_variable.source == FormVariableSources.component
        ):
            component = configuration_wrapper[key]
            value = as_json_data(component, value)
            if post_process_component is not None:
                value = post_process_component(
                    component, value, schema_for_post_processing
                )

        output_values[key] = value

    return JSONDocumentData(
        values=output_values,
        values_schema=values_schema,
    )
