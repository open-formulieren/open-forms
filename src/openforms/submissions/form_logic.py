from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from opentelemetry import trace

from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
    get_dynamic_configuration,
    inject_variables,
    process_visibility,
)
from openforms.formio.typing import FormioConfiguration

from .logic.actions import ActionOperation
from .logic.rules import get_rules_to_evaluate, iter_evaluate_rules

if TYPE_CHECKING:
    from .models import Submission, SubmissionStep

tracer = trace.get_tracer("openforms.submissions.form_logic")


empty = object()


@tracer.start_as_current_span(
    name="evaluate-form-logic",
    attributes={
        "span.type": "app",
        "span.subtype": "submissions",
        "span.action": "logic",
    },
)
def evaluate_form_logic(
    submission: Submission,
    step: SubmissionStep,
    unsaved_data: FormioData | None = None,
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
    5. Evaluate conditional logic
    6. Evaluate the logic rules in order, for each action in each triggered rule:

       1. If a variable value is being updated, update the data structure (also includes
          handling the clear-on-hide behaviour)
       2. Else record the action to perform to the configuration (but don't apply it
          yet!)

    7. Apply the dynamic configuration

       1. Apply the component property mutations that were recorded in 6
       2. Interpolate the component configuration with the variables
       3. Handle custom formio types

    8. Update relevant data structures

       1. Update the variables state
       2. Create a data difference between before and after applying form logic

    :param submission: Submission instance.
    :param step: Submission-step instance.
    :param unsaved_data: Unsaved submitted data. This data is assumed to be valid, as we
      perform a conversion to the Python-type domain. Note that we fetch all the existing
      submission data from the state, so it's only necessary to pass unsaved data.

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
    submission_variables_state = submission.variables_state

    # 4. Get relevant data structures.
    if unsaved_data:
        submission_variables_state.set_values(unsaved_data)

    # This data is used to restore the value of a component when it goes from hidden ->
    # visible. It should include all fields to make sure we have a value for them.
    data_for_visible_state = submission_variables_state.get_data(
        include_unsaved=True, submission_step=step
    )

    # This includes user-defined variables, static variables, and previously saved
    # (prefilled) step variables.
    data_for_evaluation = submission_variables_state.get_data(
        include_unsaved=False, include_static_variables=True
    )
    data_for_evaluation.update(data_for_visible_state)

    # Update data for evaluation.
    step_variables = submission_variables_state.get_variables_in_submission_step(
        step, include_unsaved=True
    )
    if unsaved_data:
        # If unsaved data was passed, we rely on it accurately reflecting the visible
        # state of the components, meaning hidden components with clearOnHide enabled
        # will not be present. Though note that we do execute conditional logic again as
        # an additional validation step.
        for key in step_variables:
            if key not in unsaved_data:
                data_for_evaluation.pop(key)

    # Initial data used to create a data difference at the end
    initial_data = deepcopy(data_for_evaluation)

    # 5. Evaluate conditional logic. We need to do this before evaluating backend logic
    # to make sure we are not processing with outdated data. The frontend will not send
    # data for fields that were (conditionally) hidden, so simply applying the unsaved
    # data to the state will not remove existing values of those fields.
    evaluate_conditional_logic(
        config_wrapper.configuration,
        data_for_evaluation,
        config_wrapper,
    )

    # 6. Evaluate the logic rules in order
    rules = get_rules_to_evaluate(submission, step)
    mutation_operations = []

    # 6.1 If the action type is to set a variable, update the data. This happens inside
    # of iter_evaluate_rules.
    with (
        tracer.start_as_current_span(
            name="collect-logic-operations",
            attributes={
                "span.type": "app",
                "span.subtype": "submissions",
                "span.action": "logic",
            },
        ),
    ):
        for operation in iter_evaluate_rules(
            rules,
            data_for_evaluation,
            data_for_visible_state,
            config_wrapper,
            submission=submission,
        ):
            mutation_operations.append(operation)

    # 7. Apply the dynamic configuration

    # we need to apply the context-specific configurations before we can apply
    # mutations based on logic, which is then in turn passed to the serializer(s)
    config_wrapper = get_dynamic_configuration(
        config_wrapper,
        submission=submission,
        data=data_for_evaluation,
    )

    # 7.1 Apply the component mutation operations
    for mutation in mutation_operations:
        mutation.apply(step, config_wrapper)

    # 7.2 Interpolate the component configuration with the variables.
    inject_variables(config_wrapper, data_for_evaluation)

    # 7.3 Handle custom formio types
    # TODO: this needs to be lifted out of :func:`get_dynamic_configuration` so that it
    #  can use variables.

    # 8. Form evaluation completed
    # 8.1 All the processing is now complete, so we can update the state.
    submission_variables_state.set_values(data_for_evaluation)

    # 8.2 Build a difference in data for the step. It is important that we only keep the
    # changes in the data, so that old values do not overwrite otherwise debounced
    # client-side data changes
    updated_step_data = FormioData()
    for key, variable in step_variables.items():
        if key not in data_for_evaluation:
            # Value was cleared, so we need to reset the variable in the state
            variable.set_undefined()
            continue

        if (
            not variable.form_variable
            or initial_data.get(key, empty) != data_for_evaluation[key]
        ):
            updated_step_data[key] = data_for_evaluation[key]
    step.unsaved_data = updated_step_data

    step._form_logic_evaluated = True

    return config_wrapper.configuration


def evaluate_conditional_logic(
    configuration: FormioConfiguration,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
):
    """
    Evaluate conditional logic through iteration.

    Note that this assumes the data converges to a final state, so no cycles can be
    present in the complete conditional logic tree.

    :param configuration: Formio configuration.
    :param data: Data used for evaluation. Mutations will be applied to the data
      directly.
    :param wrapper: Formio configuration wrapper. Required for component lookup.
    """
    processed_data = None
    _loop_count = 0
    while processed_data != data:
        if _loop_count >= 50:  # pragma: nocover
            raise RuntimeError("Potential infinite loop stopped!")
        _loop_count += 1
        processed_data = deepcopy(data)
        process_visibility(configuration, data, wrapper)


def check_submission_logic(
    submission: Submission,
    *,
    reset_configuration_wrapper: bool = True,
    evaluate_all_rules: bool = False,
) -> None:
    if getattr(submission, "_form_logic_evaluated", False):
        return

    submission_state = submission.load_execution_state()
    # if there are no form steps at all, then there's nothing to do
    if not submission_state.form_steps:
        return

    rules = get_rules_to_evaluate(submission, evaluate_all_rules=evaluate_all_rules)

    # load the data state and all variables
    submission_variables_state = submission.variables_state
    data_for_evaluation = submission_variables_state.get_data(
        include_unsaved=False, include_static_variables=True
    )

    mutation_operations: list[ActionOperation] = []
    # Note: values should have already been resolved at this point, so we just pass
    # `data_for_evaluation` as data for visible state.
    for operation in iter_evaluate_rules(
        rules,
        data_for_evaluation,
        data_for_evaluation,
        submission.total_configuration_wrapper,
        submission,
    ):
        mutation_operations.append(operation)

    submission_variables_state.set_values(data_for_evaluation)

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

    # Note that the total configuration wrapper is a cached property, so we need to
    # reset to ensure we are not operating on outdated configurations later.
    # XXX: not sure why this is necessary - removing it entirely doesn't seem to break
    # any tests? Check with Viktor.
    if reset_configuration_wrapper:
        submission._total_configuration_wrapper = None
    submission._form_logic_evaluated = True
