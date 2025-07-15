from typing import TYPE_CHECKING

from django.utils.functional import empty

import elasticapm

from openforms.formio.service import (
    FormioData,
    get_dynamic_configuration,
    inject_variables,
)
from openforms.formio.typing import FormioConfiguration
from openforms.formio.utils import get_component_empty_value

from .logic.actions import ActionOperation
from .logic.rules import get_rules_to_evaluate, iter_evaluate_rules
from .models.submission_step import DirtyData

if TYPE_CHECKING:
    from .models import Submission, SubmissionStep


@elasticapm.capture_span(span_type="app.submissions.logic")
def evaluate_form_logic(
    submission: "Submission",
    step: "SubmissionStep",
    data: FormioData,
) -> FormioConfiguration:
    """
    Process all the form logic rules and mutate the step configuration if required.

    The form logic evaluation is split up in multiple stages to achieve a deterministic
    output while respecting the ordering of logic rules. The logic evaluation has a
    number of side effects:

    * setting/writing values for variables
    * dynamic Formio configuration updates, based on the variable values
    * dynamic Formio configuration updates, based on the logic actions

    We achieve this by:

    1. Loading the submission and submission step (passed as function arguments)
    2. Prefilled data is saved at submission start and available in the variables
    3. Loading the variable state, which populates non-saved values with their defaults
    4. Apply any dirty data (unsaved) to the variable state
    5. Evaluate the logic rules in order, for each action in each triggered rule:

       1. If a variable value is being updated, update the data structure
       2. Else record the action to perform to the configuration (but don't apply it yet!)

    6. Apply the dynamic configuration

       1. Apply the component property mutations that were recorded in 5
       2. Handle the 'clearOnHide' property
       3. Interpolate the component configuration with the variables
       4. Handle custom formio types

    7. Update relevant data structures

       1. Update the variables state
       2. Create a data difference between before and after applying form logic

    :param submission: Submission instance.
    :param step: Submission-step instance.
    :param data: Submitted data. This data is assumed to be valid, as we perform a
      conversion to the Python-type domain.

    """
    # grab the configuration that will be mutated
    config_wrapper = step.form_step.form_definition.configuration_wrapper
    # 1. we have `submission` and `step` available and ...
    # 2. the prefilled variables are already recorded in the variables state
    #
    # The Formio *default values* are also recorded in here, because the `FormVariable`
    # for each component derives that from the configuration at save-time.

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return config_wrapper.configuration

    # 3. Load the (variables) state
    submission_variables_state = submission.load_submission_value_variables_state()

    # 4. Apply the (dirty) data to the variable state.
    submission_variables_state.set_values(data)
    initial_data = submission_variables_state.get_data(
        include_unsaved=True, include_static_variables=True
    )
    data_for_evaluation = submission_variables_state.get_data(
        include_unsaved=True, include_static_variables=True
    )

    rules = get_rules_to_evaluate(submission, step)

    # 5. Evaluate the logic rules in order
    mutation_operations = []

    # 5.1 If the action type is to set a variable, update the data. This happens inside
    # of iter_evaluate_rules. This is the ONLY operation that is allowed to execute
    # while we're looping through the rules.
    data_diff = FormioData()
    with elasticapm.capture_span(
        name="collect_logic_operations", span_type="app.submissions.logic"
    ):
        for operation, mutations in iter_evaluate_rules(
            rules,
            data_for_evaluation,
            submission=submission,
        ):
            mutation_operations.append(operation)
            if mutations:
                data_diff.update(mutations)

    # 6. Apply the dynamic configuration

    # we need to apply the context-specific configurations before we can apply
    # mutations based on logic, which is then in turn passed to the serializer(s)
    config_wrapper = get_dynamic_configuration(
        config_wrapper,
        submission=submission,
        data=data_for_evaluation,
    )

    # 6.1 Apply the component mutation operations
    for mutation in mutation_operations:
        mutation.apply(step, config_wrapper)

    # 6.2 Handle 'clearOnHide' property
    # XXX: See #2340 and #2409 - we need to clear the values of components that are
    # (eventually) hidden BEFORE we do any further processing. This is only a bandaid
    # fix, as the (stale) data has potentially been input for other logic rules.
    # Note that only the dirty data logic check acts on these differences.
    for component in config_wrapper:
        key = component["key"]
        is_visible = config_wrapper.is_visible_in_frontend(key, data_for_evaluation)
        if is_visible:
            continue

        # Reset the value of any field that may have become hidden again after
        # evaluating the logic
        original_value = initial_data.get(key, empty)
        empty_value = get_component_empty_value(component)
        if original_value is empty or original_value == empty_value:
            continue

        if not component.get("clearOnHide", True):
            continue

        # clear the value
        data_for_evaluation[key] = empty_value
        data_diff[key] = empty_value

    # 6.3 Interpolate the component configuration with the variables.
    inject_variables(config_wrapper, data_for_evaluation)

    # 6.4 Handle custom formio types
    # TODO: this needs to be lifted out of :func:`get_dynamic_configuration` so that it
    #  can use variables.

    # 7. Form evaluation completed
    # 7.1 All the processing is now complete, so we can update the state.
    submission_variables_state.set_values(data_diff)

    # 7.2 Build a difference in data for the step. It is important that we only keep the
    # changes in the data, so that old values do not overwrite otherwise debounced
    # client-side data changes

    # Get relevant step variables
    relevant_variables = submission_variables_state.get_variables_in_submission_step(
        step, include_unsaved=True
    )

    # NOTE: we cannot use `data_diff` as it might contain mutations that are equal to
    # the original value of the variable. For example, when the same variable was
    # changed by two separate logic actions back to its original value, it would show
    # up in the `data_diff` but it shouldn't be returned (set to `SubmissionStep.data`)
    updated_step_data = FormioData()
    for key, variable in relevant_variables.items():
        if not variable.form_variable or initial_data[key] != data_for_evaluation[key]:
            updated_step_data[key] = data_for_evaluation[key]
    step.data = DirtyData(updated_step_data)

    step._form_logic_evaluated = True

    return config_wrapper.configuration


def check_submission_logic(
    submission: "Submission",
    current_step: "SubmissionStep | None" = None,
) -> None:
    if getattr(submission, "_form_logic_evaluated", False):
        return

    submission_state = submission.load_execution_state()
    # if there are no form steps at all, then there's nothing to do
    if not submission_state.form_steps:
        return

    rules = get_rules_to_evaluate(submission, current_step)

    # load the data state and all variables
    submission_variables_state = submission.load_submission_value_variables_state()
    data_for_evaluation = submission_variables_state.get_data(
        include_unsaved=True, include_static_variables=True
    )

    mutation_operations: list[ActionOperation] = []
    data_diff = FormioData({})
    for operation, mutations in iter_evaluate_rules(
        rules, data_for_evaluation, submission
    ):
        mutation_operations.append(operation)
        if mutations:
            data_diff.update(mutations)

    submission_variables_state.set_values(data_diff)

    # we loop over all steps because we have validations that ensure unique component
    # keys across multiple steps for the whole form.
    #
    # We need to apply all component mutations at this stage too, because for validation
    # reasons, a serializer is built from them.
    for mutation in mutation_operations:
        for step in submission_state.submission_steps:
            assert step.form_step
            configuration = step.form_step.form_definition.configuration_wrapper
            mutation.apply(step, configuration)

    submission._form_logic_evaluated = True
