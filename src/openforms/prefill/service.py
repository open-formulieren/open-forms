"""
This package holds the base module structure for the pre-fill plugins used in Open Forms.

Various sources exist that can be consulted to fetch data for an active session,
where the BSN, CoC number... can be used to retrieve this data. Think of pre-filling
the address details of a person after logging in with DigiD.

The package integrates with the form builder such that it's possible for every form
field to a) select which pre-fill plugin to use and which value to use from the fetched
result and b) define a user-defined variable in which the ``prefill_options`` are configured.
Plugins can be registered using a similar approach to the registrations
package. Each plugin is responsible for exposing which attributes/data fragments are
available, and for performing the actual look-up. Plugins receive the
:class:`openforms.submissions.models.Submission` instance that represents the current
form session of an end-user.

Prefill values are embedded as default values for form fields, dynamically for every
user session using the component rewrite functionality in the serializers.

So, to recap:

1. Plugins are defined and registered
2. When editing form definitions in the admin, content editors can opt-in to pre-fill
   functionality. They select the desired plugin, and then the desired attribute from
   that plugin.
3. Content editors can also define a user-defined variable and configure the plugin and
   the necessary options by selecting the desired choices for the ``prefill_options``.
4. End-user starts the form and logs in, thereby creating a session/``Submission``
5. The submission-specific form definition configuration is enhanced with the pre-filled
   form field default values.
"""

import logging
from collections import defaultdict

import elasticapm

from openforms.formio.service import FormioConfigurationWrapper
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable
from openforms.variables.constants import FormVariableSources

from .registry import Registry
from .sources.component import (
    fetch_prefill_values as fetch_prefill_values_for_component,
)
from .sources.user_defined import (
    fetch_prefill_values as fetch_prefill_values_for_user_defined,
)

logger = logging.getLogger(__name__)


def inject_prefill(
    configuration_wrapper: FormioConfigurationWrapper, submission: Submission
) -> None:
    """
    Mutates each component found in configuration according to the prefilled values.

    :param configuration_wrapper: The Formiojs JSON schema wrapper describing an entire
    form or an individual component within the form.
    :param submission: The :class:`openforms.submissions.models.Submission` instance
    that holds the values of the prefill data. The prefill data was fetched earlier,
    see :func:`prefill_variables`.

    The prefill values are looped over by key: value, and for each value the matching
    component is looked up to normalize it in the context of the component.
    """

    from openforms.formio.service import normalize_value_for_component

    prefilled_data = submission.get_prefilled_data()
    for key, prefill_value in prefilled_data.items():
        try:
            component = configuration_wrapper[key]
        except KeyError:
            # The component to prefill is not in this step
            continue

        if not (prefill := component.get("prefill")):
            continue
        if not prefill.get("plugin"):
            continue
        if not prefill.get("attribute"):
            continue

        default_value = component.get("defaultValue")
        # 1693: we need to normalize values according to the format expected by the
        # component. For example, (some) prefill plugins return postal codes without
        # space between the digits and the letters.
        prefill_value = normalize_value_for_component(component, prefill_value)

        if prefill_value != default_value and default_value is not None:
            logger.info(
                "Overwriting non-null default value for component %r",
                component,
            )
        component["defaultValue"] = prefill_value


@elasticapm.capture_span(span_type="app.prefill")
def prefill_variables(submission: Submission, register: Registry | None = None) -> None:
    """Update the submission variables state with the fetched attribute values.

    For each submission value variable that need to be prefilled, the according plugin will
    be used to fetch the value. If ``register`` is not specified, the default registry instance
    will be used.
    """
    from openforms.formio.service import normalize_value_for_component

    from .registry import register as default_register

    register = register or default_register

    state = submission.load_submission_value_variables_state()
    variables_to_prefill = state.get_prefill_variables()

    component_variables: list[SubmissionValueVariable] = []
    user_defined_variables: list[SubmissionValueVariable] = []
    prefill_data: defaultdict[str, JSONEncodable] = defaultdict(dict)

    for variable in variables_to_prefill:
        if (
            variable.form_variable.source == FormVariableSources.component
            and variable.form_variable.prefill_attribute
        ):
            component_variables.append(variable)
        elif (
            variable.form_variable.source == FormVariableSources.user_defined
            and variable.form_variable.prefill_options
        ):
            user_defined_variables.append(variable)

    if component_variables and (
        component_results := fetch_prefill_values_for_component(
            submission, register, component_variables
        )
    ):
        prefill_data.update(**component_results)
    if user_defined_variables and (
        user_defined_results := fetch_prefill_values_for_user_defined(
            submission, register, user_defined_variables
        )
    ):
        prefill_data.update(**user_defined_results)

    total_config_wrapper = submission.total_configuration_wrapper
    for variable_key, prefill_value in prefill_data.items():
        component = total_config_wrapper[variable_key]
        normalized_prefill_value = normalize_value_for_component(
            component, prefill_value
        )
        variable = state.get_variable(variable_key)
        variable.value = normalized_prefill_value
        prefill_data[variable_key] = normalized_prefill_value

    state.save_prefill_data(prefill_data)
