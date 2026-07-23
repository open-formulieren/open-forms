"""
This package holds the base module structure for the pre-fill plugins used in Open Forms.

Various sources exist that can be consulted to fetch data for an active session,
where the BSN, CoC number... can be used to retrieve this data. Think of pre-filling
the address details of a person after logging in with DigiD.

The package integrates with the form builder such that it's possible to:
    a) select which pre-fill plugin to use and which value to use from the fetched
    result via the component's configuration,
    b) create a user-defined variable via the variables tab and select which pre-fill plugin
    to use and which value to use from the fetched result and
    c) define a user-defined variable via the variables tab in which the ``prefill_options``
    are configured.

Plugins can be registered using a similar approach to the registrations package. Each plugin
is responsible for exposing which attributes/data fragments are available, and for performing
the actual look-up. Plugins receive the :class:`openforms.submissions.models.Submission`
instance that represents the current form session of an end-user.

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

from typing import Protocol

import structlog
from opentelemetry import trace
from typing_extensions import TypeIs

from formio_types import TYPE_TO_TAG, AnyComponent
from formio_types._base import Prefill
from openforms.formio.service import (
    FormioConfig,
    FormioData,
)
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable
from openforms.variables.constants import FormVariableSources

from .registry import Registry, register as default_register
from .sources import (
    fetch_prefill_values_from_attribute,
    fetch_prefill_values_from_options,
)

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.prefill.service")


class ComponentWithPrefill(Protocol):
    prefill: Prefill | None = None


# The TypeIs narrowing doesn't play nice with union types :(
def has_prefill(component: AnyComponent) -> TypeIs[ComponentWithPrefill]:  # pyright: ignore[reportGeneralTypeIssues]
    prefill = getattr(component, "prefill", None)
    return isinstance(prefill, Prefill)


def inject_prefill(config: FormioConfig, submission: Submission) -> None:
    """
    Mutates each component found in configuration according to the prefilled values.

    :param config: The Formiojs JSON schema wrapper describing an entire form.
    :param submission: The :class:`openforms.submissions.models.Submission` instance
      that holds the values of the prefill data. The prefill data was fetched earlier,
      see :func:`prefill_variables`.

    The prefill values are looped over by key: value, and for each value the matching
    component is looked up to normalize it in the context of the component.
    """
    state = submission.variables_state
    prefilled_data = state.get_prefilled_data()
    for key, variable in state.prefilled_variables.items():
        # The component to prefill is not in this step
        if key not in config:
            continue
        prefill_value = prefilled_data[key]
        component = config[key]

        # ignore components that don't support or have prefill configuration
        if not has_prefill(component):
            continue

        if (
            not (prefill := component.prefill)
            or not prefill.plugin
            or not prefill.attribute
        ):
            continue

        # Prefill values fetched from the state are in native Python types, so we need
        # to convert the default value before doing a comparison.
        default_value = variable.to_python(component.default_value)

        if prefill_value != default_value and default_value is not None:
            logger.info(
                "prefill.overwrite_non_null_default_value",
                submission_uuid=str(submission.uuid),
                component_type=TYPE_TO_TAG[type(component)],
                default_value=default_value,
                component_id=component.id,
                component_key=component.key,
            )
        # Component configuration is still in JSON, so we need to convert the value
        # back. Would be nice if this was no longer necessary with the (maybe planned)
        # formio configuration msgspec rework :)
        # TODO: set_default_value method to handle the typing issues/consistency?
        # Cleaner would be to have prefill not set default value at all, and instead
        # store it in the target variables to begin with.
        component.default_value = variable.to_json(prefill_value)


@tracer.start_as_current_span(
    name="prefill-variables", attributes={"span.type": "app", "span.subtype": "prefill"}
)
def prefill_variables(submission: Submission, register: Registry | None = None) -> None:
    """
    Update the submission variables state with the fetched attribute values.

    For each submission value variable that needs to be prefilled, the according plugin
    will be used to fetch the value. If ``register`` is not specified, the default
    registry instance will be used.
    """
    register = register or default_register
    state = submission.variables_state

    with structlog.contextvars.bound_contextvars(submission_pk=submission.pk):
        variables_with_attribute: list[SubmissionValueVariable] = []
        variables_with_options: list[SubmissionValueVariable] = []
        prefill_data: dict[str, JSONEncodable] = {}

        for variable in state.prefilled_variables.values():
            form_variable = variable.form_variable
            assert form_variable is not None
            # variables which have prefill enabled via the component's configuration
            if (
                form_variable.source == FormVariableSources.component
                and form_variable.prefill_plugin
                and form_variable.prefill_attribute
            ):
                variables_with_attribute.append(variable)
                continue

            if form_variable.source == FormVariableSources.user_defined:
                # variables which have prefill enabled via the variables tab and define
                # prefill options
                if form_variable.prefill_plugin and form_variable.prefill_options:
                    variables_with_options.append(variable)

                # variables which have prefill enabled via the variables tab and define
                # prefill attribute
                if form_variable.prefill_plugin and form_variable.prefill_attribute:
                    variables_with_attribute.append(variable)

        if variables_with_attribute:
            results_from_attribute = fetch_prefill_values_from_attribute(
                submission, register, variables_with_attribute
            )
            prefill_data.update(**results_from_attribute)

        if variables_with_options:
            results_from_options = fetch_prefill_values_from_options(
                submission, register, variables_with_options
            )
            prefill_data.update(**results_from_options)

        state.save_prefill_data(FormioData(prefill_data))
