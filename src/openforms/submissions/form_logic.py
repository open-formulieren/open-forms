from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict

import elasticapm
from json_logic import jsonLogic

from openforms.formio.service import get_dynamic_configuration, inject_variables
from openforms.formio.utils import (
    get_component,
    get_component_default_value,
    is_visible_in_frontend,
)
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic
from openforms.logging import logevent

from .logic.actions import compile_action_operation
from .logic.datastructures import DataContainer
from .models.submission_step import DirtyData

if TYPE_CHECKING:  # pragma: nocover
    from .models import Submission, SubmissionStep


@elasticapm.capture_span(span_type="app.submissions.logic")
def evaluate_form_logic(
    submission: "Submission",
    step: "SubmissionStep",
    data: Dict[str, Any],
    dirty=False,
    **context,
) -> Dict[str, Any]:
    """
    Process all the form logic rules and mutate the step configuration if required.

    The form logic evaluation is split up in multiple stages to achieve a deterministic
    output while respecting the ordering of logic rules. The logic evaluation has a
    number of side effects:

    * setting/writing values for variables
    * dynamic Formio configuration updates, based on the variable values
    * dynamic Formio configuration updates, based on the logic actions
    * dynamic Formio configuration based on the request context

    We achieve this by:

    1. Loading the submission and submission step (passed as function arguments)
    2. Prefilled data is saved at submission start and available in the variables
    3. Loading the variable state, which populates non-saved values with their defaults.
    4. Apply any dirty data (unsaved) to the variable state
    5. Evaluate the logic rules in order, for each action in each triggered rule:

       1. If a variable value is being update, update the variable state
       2. Else record the action to perform to the configuration (but don't apply it yet!)

    6. The variables state is now completely resolved and can be used as input for the
       dynamic configuration.
    7. Apply the dynamic configuration

       1. Apply the component property mutations that were recorded in 5.
       2. Interpolate the component configuration with the variables.
       3. Handle custom formio types (which require variables as input!)

    """
    # grab the configuration that will be mutated
    configuration = step.form_step.form_definition.configuration

    # 1. we have `submission` and `step` available and ...
    # 2. the prefilled variables are already recorded in the variables state
    #
    # The Formio *default values* are also recorded in here, because the `FormVariable`
    # for each component derives that from the configuration at save-time.
    #
    if not step.data:
        step.data = DirtyData({})

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return configuration

    # 3. Load the (variables) state
    submission_state = submission.load_execution_state()
    submission_variables_state = submission.load_submission_value_variables_state()

    # 4. Apply the (dirty) data to the variable state.
    submission_variables_state.set_values(data)

    # renderer evaluates logic for all steps at once, so we can avoid repeated queries
    # by caching the rules on the form instance.
    # Note that form.formlogic_set.all() is never cached by django, so we can't rely
    # on that.
    rules = getattr(submission.form, "_cached_logic_rules", None)
    if rules is None:
        rules = FormLogic.objects.select_related("trigger_from_step").filter(
            form=submission.form
        )
        submission.form._cached_logic_rules = rules

    step_index = submission_state.form_steps.index(step.form_step)

    data_container = DataContainer(state=submission_variables_state)

    # 5. Evaluate the logic rules in order
    mutation_operations = []
    evaluated_rules = []

    for rule in rules:
        # only evaluate a logic rule if it either:
        # - is not limited to a particular trigger point/step
        # - is limited to a particular trigger point/step and the current submission step
        #   is equal to or later than the trigger point
        if rule.trigger_from_step:
            trigger_from_index = submission_state.form_steps.index(
                rule.trigger_from_step
            )
            if step_index < trigger_from_index:
                continue

        trigger_rule = jsonLogic(rule.json_logic_trigger, data_container.data)
        evaluated_rules.append({"rule": rule, "trigger": bool(trigger_rule)})
        # rule is not triggered - do not process the actions.
        if not trigger_rule:
            continue

        # process all the actions in order for the triggered rule
        for action in rule.actions:
            action_details = action["action"]

            # 5.1 - if the action type is to set a variable, update the variable state.
            # This is the ONLY operation that is allowed to execute while we're looping
            # through the rules.
            if action_details["type"] == LogicActionTypes.variable:
                new_value = jsonLogic(action_details["value"], data_container.data)
                data_container.update({action["variable"]: new_value})
            else:
                operation = compile_action_operation(action)
                mutation_operations.append(operation)

    # 6. The variable state is now completely resolved - we can start processing the
    # dynamic configuration and side effects.

    # Calculate which data has changed from the initial, for the step.
    updated_step_data = data_container.get_updated_step_data(step)
    step.data = DirtyData(updated_step_data)

    # 7. finally, apply the dynamic configuration

    # we need to apply the context-specific configurations before we can apply
    # mutations based on logic, which is then in turn passed to the serializer(s)
    # TODO: refactor this to rely on variables state, which will move this down to
    configuration = deepcopy(configuration)
    configuration = get_dynamic_configuration(
        configuration,
        # context is expected to contain request, as is the default behaviour with DRF
        # view(set)s and serializers. Note that :func:`get_dynamic_configuration` is
        # planned for refactor as part of #1068, which should drop the ``request``
        # argument. The required information is available on the ``submission`` object
        # already.
        request=context.get("request"),
        submission=submission,
    )

    # 7.1 Apply the component mutation operations
    for mutation in mutation_operations:
        mutation.apply(step, configuration)

    # 7.2 Interpolate the component configuration with the variables.
    inject_variables(configuration, data_container.data)

    # 7.3 Handle custom formio types - TODO: this needs to be lifted out of
    # :func:`get_dynamic_configuration` so that it can use variables.

    # Logging the rules
    initial_data = data_container.initial_data
    logevent.submission_logic_evaluated(
        submission,
        evaluated_rules,
        initial_data,
        data_container.data,
    )

    # process the output for logic checks with dirty data
    if dirty:
        # only keep the changes in the data, so that old values do not overwrite otherwise
        # debounced client-side data changes
        data_diff = {}

        for key, new_value in step.data.items():
            original_value = initial_data.get(key)
            # Reset the value of any field that may have become hidden again after evaluating the logic
            if original_value:
                component = get_component(configuration, key)
                default = get_component_default_value(component)
                if (
                    component
                    and not is_visible_in_frontend(component, data_container.data)
                    and component.get("clearOnHide")
                ):
                    data_diff[key] = default or ""
                    continue

            if new_value == original_value:
                continue
            data_diff[key] = new_value

        # only return the 'overrides'
        step.data = DirtyData(data_diff)

    step._form_logic_evaluated = True

    return configuration


def check_submission_logic(submission, unsaved_data=None):
    # TODO: https://github.com/open-formulieren/open-forms/issues/1913
    logic_rules = FormLogic.objects.filter(
        form=submission.form,
        actions__contains=[{"action": {"type": LogicActionTypes.step_not_applicable}}],
    )

    merged_data = submission.data
    if unsaved_data:
        merged_data = {**merged_data, **unsaved_data}

    submission_state = submission.load_execution_state()

    for rule in logic_rules:
        if jsonLogic(rule.json_logic_trigger, merged_data):
            for action in rule.actions:
                # TODO: this should not be necessary because of the query filter above?
                # but perhaps we might want to re-use the logic rules cached on the
                # submission instance?
                if action["action"]["type"] != LogicActionTypes.step_not_applicable:
                    continue

                submission_step_to_modify = submission_state.resolve_step(
                    action["form_step"]
                )
                submission_step_to_modify._is_applicable = False
