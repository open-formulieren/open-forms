from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from django.utils.functional import empty

import elasticapm

from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
    get_dynamic_configuration,
    inject_variables,
)
from openforms.formio.typing import (
    Component,
    ConditionalCompareValue,
    FormioConfiguration,
)
from openforms.formio.utils import (
    ComponentLike,
    get_component_empty_value,
    iter_components,
)

from .logic.actions import ActionOperation
from .logic.rules import get_rules_to_evaluate, iter_evaluate_rules
from .models.submission_step import DirtyData

if TYPE_CHECKING:
    from .models import Submission, SubmissionStep


@elasticapm.capture_span(span_type="app.submissions.logic")
def evaluate_form_logic(
    submission: Submission,
    step: SubmissionStep,
    unsaved_data: FormioData | None = None,
    use_new_behaviour=False,
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
    submission_variables_state = submission.load_submission_value_variables_state()

    # 4. Apply the (dirty) data to the variable state.
    if unsaved_data is not None:
        submission_variables_state.set_values(unsaved_data)
    data_for_evaluation = submission_variables_state.get_data(
        include_unsaved=True, include_static_variables=True
    )

    # 5. Evaluate conditional logic. We need to do this before evaluating backend logic
    # to make sure we are not processing with outdated data. The frontend will not send
    # data for fields that were conditionally hidden, so applying the incoming unsaved
    # data to the state will not set the values of those fields to empty.
    if use_new_behaviour:
        evaluate_conditional_logic(
            config_wrapper.configuration, data_for_evaluation, config_wrapper
        )
    initial_data = deepcopy(data_for_evaluation)

    # 5. Evaluate the logic rules in order
    rules = get_rules_to_evaluate(submission, step)

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
        if use_new_behaviour:
            break

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
    submission_variables_state.set_values(data_for_evaluation)

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


def get_conditional(
    component: Component,
) -> tuple[bool, str, ConditionalCompareValue] | None:
    conditional = component.get("conditional")
    if not conditional:
        return None

    show = conditional.get("show")
    when = conditional.get("when")
    eq = conditional.get("eq")

    if any([show is None, when is None, eq is None]):
        return None

    return show, when, eq


def is_hidden_by_conditional(
    component: Component, data: FormioData, configuration: FormioConfigurationWrapper
) -> bool:
    conditional = get_conditional(component)

    # Note that the previous (and frontend) implementation also checked the "hidden"
    # property, but we cannot do that in this case, as it might result in values being
    # cleared that shouldn't. For example, a field that is hidden by default and shown
    # with a logic rule will have its value always cleared if this is executed before
    # logic rule evaluation. All of this is assuming we evaluate conditional logic
    # BEFORE backend logic.
    if conditional is None:
        return False

    show, trigger_component_key, compare_value = conditional

    trigger_component_value = data.get(trigger_component_key, None)
    trigger_component = configuration[trigger_component_key]

    # TODO-5134: move to registry
    match trigger_component:
        case {"type": "selectboxes"}:
            # Selectboxes need some special attention as we need to check whether the
            # compare value is set to `True` in the dictionary.
            # NOTE: the previous implementation defaulted to the direct comparison, but
            # this is not useful for selectboxes components, because a user can only set
            # a single compare value, not an object.
            trigger = trigger_component_value.get(compare_value, False)

        case _:
            if trigger_component.get("multiple", False):
                assert isinstance(trigger_component_value, list)
                trigger = compare_value in trigger_component_value
            else:
                trigger = trigger_component_value == compare_value

    # Note that we return whether the component is hidden, not shown, so we invert the
    # return value
    return not show if trigger else show


def process_visibility(
    configuration: ComponentLike,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
    parent_hidden: bool = False,
    parent_path: str = "",
):
    """Because this is executed inside ``evaluate_form_logic``, we can mutate ``data``
    directly. The data diff will be built up at the end of evaluating logic.
    """
    for component in iter_components(
        configuration, recursive=False, recurse_into_editgrid=False
    ):
        key = component["key"]
        path = f"{parent_path}.{key}" if parent_path else key
        clear_on_hide = component.get("clearOnHide", True)
        hidden = parent_hidden or is_hidden_by_conditional(component, data, wrapper)

        if hidden and clear_on_hide:
            # Need to perform this check because fieldset, columns, softRequiredErrors,
            # and content components have no value
            # TODO-5134: this might mask bugs? Perhaps better to explicitly check for
            #  these components?
            if path in data:
                empty_value = get_component_empty_value(component)
                data[path] = empty_value

        # TODO-5134: might move to the component plugins and access through the
        #  registry?
        match component["type"]:
            case "fieldset":
                # We need to process the children
                process_visibility(component, data, wrapper, hidden, parent_path)
            case "columns":
                # Create an artificial flat component list to make processing easier.
                # The alternative is to pass `recursive` as an argument to
                # `iter_components`
                config_new = {
                    "components": [
                        child
                        for column in component["columns"]
                        for child in column["components"]
                    ]
                }
                process_visibility(config_new, data, wrapper, hidden, parent_path)
            case "editgrid":
                # We only need to process children if the value was not already cleared.
                if not (edit_grid_data := data[path]):
                    continue

                data_new = []
                for entry in edit_grid_data:
                    # For a simple conditional, a reference to a field inside an
                    # editgrid will be formatted as "editgrid_key.nested_key", so we
                    # create 'fake' data to ensure we can reason within each editgrid
                    # entry.
                    entry_data = FormioData({key: entry})

                    process_visibility(component, entry_data, wrapper, hidden, key)
                    data_new.append(entry_data[key])

                data[path] = data_new


# TODO-5134: probably be good to also update the hidden property of the configuration.
#  The backend might send an outdated different configration to the frontend if we don't
def evaluate_conditional_logic(
    configuration: ComponentLike,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
):
    """Evaluate conditional logic.

    Note that this assumes the data converges to a final state, so no cycles can be
    present in the complete conditional logic tree.

    :param configuration:
    :param data:
    :param wrapper:
    :return:
    """
    # TODO-5134: if performance will be a problem, we could search for all components
    #  that have a (valid) conditional configured, and only process those.
    initial_data = None
    while initial_data != data:
        initial_data = deepcopy(data)
        process_visibility(configuration, data, wrapper)


def check_submission_logic(
    submission: Submission,
    current_step: SubmissionStep | None = None,
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
