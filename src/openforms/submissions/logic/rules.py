from collections.abc import Iterable, Iterator
from itertools import chain

from json_logic import jsonLogic
from opentelemetry import trace

from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
    process_visibility,
)
from openforms.forms.models import FormLogic

from ..models import Submission, SubmissionStep
from .actions import ActionOperation
from .log_utils import log_errors

tracer = trace.get_tracer("openforms.submissions.logic.rules")


def get_rules_to_evaluate(
    submission: Submission,
    current_step: SubmissionStep | None = None,
    *,
    evaluate_all_rules: bool = False,
) -> Iterable[FormLogic]:
    """
    Given a submission, return the logic rules ready for evaluation.

    The logic rules are fetched from a many-to-many field on the form step.

    :param submission: A submission instance to retrieve the rules for
    :param current_step: The (optional) step at which the rules need to be evaluated. If
      not provided, the step following the last completed step is used, or the first
      step in the form if there are no completed steps.
    :param evaluate_all_rules: If ``True``, don't limit the returned rules to the
      current submission step.
    :returns: An iterable of :class`openforms.forms.models.FormLogic` instances. This
      may be a queryset, but could also be a list.
    """
    submission_state = submission.load_execution_state()
    # if there are no form steps, there is no usable form -> there are no logic rules
    # to evaluate
    if not (form_steps := submission_state.form_steps):
        return []

    if evaluate_all_rules:
        # ensure the rules are returned in order of the form steps
        rules = chain.from_iterable(
            form_step.logic_rules.all() for form_step in form_steps
        )
        return rules

    # filter down the rules that are only applicable in the current step context
    current_step = current_step or get_current_step(submission)
    assert current_step is not None  # we already exit early if there are no form steps

    # Note that this an OrderedModelQuerySet, so the logic order is already resolved
    # here
    return current_step.form_step.logic_rules.all()


def get_current_step(submission: Submission) -> SubmissionStep | None:
    """
    Obtain what the 'current step' of a submission is.

    The current step is defined as the step following the last completed step. Note
    that this does not evaluate any logic, so if this step happens to be made
    not-applicable dynamically, it will still be returned.

    If the last completed step is the last step in the form, then this step is returned.

    :param submission: The submission instance to get the current step for.
    :returns: None if there are no steps in the form, otherwise the first submission
      step that isn't completed.
    """
    submission_state = submission.load_execution_state()
    if not submission_state.form_steps:
        return

    last_completed_step = submission_state.get_last_completed_step()
    # no steps completed -> current index is first step: 0
    if last_completed_step is None:
        current_index = 0
    else:
        last_completed_step_index = submission_state.form_steps.index(
            last_completed_step.form_step
        )
        current_index = min(
            last_completed_step_index + 1, len(submission_state.form_steps) - 1
        )

    step = submission_state.submission_steps[current_index]
    return step


def iter_evaluate_rules(
    rules: Iterable[FormLogic],
    data: FormioData,
    data_for_visible_state: FormioData,
    configuration: FormioConfigurationWrapper,
    submission: Submission,
) -> Iterator[ActionOperation]:
    """
    Iterate over the rules and evaluate the trigger, yielding action operations and
    mutations.

    Every rule trigger is checked, and if the trigger evaluates to be truthy, all
    actions in the rule are compiled, yielding action operations for each of them. Any
    action operator that updates a variable is processed immediately. The caller is
    responsible for processing (all other) actions accordingly.

    :param rules: An iterable of form logic rules to evaluate.
    :param data: Mapping from variable key to variable value (native Python types), for
      all variables present in the :class:`SubmissionValueVariableState`. This data
      structure is updated after every mutation.
    :param data_for_visible_state: The data used to restore values when flipping
      visibility states.
    :param configuration: Formio configuration wrapper of a step.
    :param submission: Submission instance.
    :returns: An iterator yielding :class:`ActionOperation` instances.
    """
    state = submission.variables_state

    for rule in rules:
        with (
            tracer.start_as_current_span(
                name="evaluate-rule",
                attributes={
                    "span.type": "app",
                    "span.subtype": "submissions",
                    "span.action": "logic",
                    "ruleId": rule.pk,
                },
            ),
        ):
            triggered = False
            with log_errors(rule.json_logic_trigger, rule):
                triggered = bool(
                    jsonLogic(
                        rule.json_logic_trigger,
                        data.data,  # pyright: ignore[reportArgumentType]
                        use_var_undefined=True,
                    )
                )

            # If the rule was not triggered, we still need to handle the clear on hide,
            # as components can be hidden by default and shown when a logic rule is
            # triggered
            if not triggered:
                _handle_clear_on_hide_for_untriggered_rule(
                    rule,
                    data,
                    configuration,
                    data_for_visible_state=data_for_visible_state,
                )
                continue

            for operation in rule.action_operations:
                if mutations := operation.eval(
                    data,
                    configuration,
                    submission,
                    data_for_visible_state=data_for_visible_state,
                ):
                    mutations_python = {
                        key: state.variables[key].to_python(value)
                        for key, value in mutations.items()
                    }
                    data.update(mutations_python)
                    # Any mutations also need to be applied to the data for the visible
                    # component state. Otherwise, the original user input data might
                    # override it when flipping visibility states.
                    data_for_visible_state.update(mutations_python)

                yield operation


def _handle_clear_on_hide_for_untriggered_rule(
    rule: FormLogic,
    data: FormioData,
    configuration: FormioConfigurationWrapper,
    *,
    data_for_visible_state: FormioData,
):
    """
    Handle clear-on-hide behaviour for components of which the "hidden" property
    actions were not triggered.

    We can do this by checking the (default) value of the "hidden" property.
    """
    for operation in rule.hidden_actions:
        # Note that this can happen when the action applies to a component of a
        # different step than we are currently evaluating. We don't have to do anything
        # in this case, because the clear-on-hide behaviour of that component will be
        # handled once the user has reached that step.
        if operation.component not in configuration:
            continue

        component = configuration[operation.component]
        # Process the visibility of the component. We want to process the component
        # itself, not try to iterate over its children, so we create a 'fake'
        # configuration.
        # When a component flips back to visible after being hidden and having its value
        # cleared before, we need to restore the original input data, so we must always
        # call this (see #6005).
        process_visibility(
            {"components": [component]},
            data,
            configuration,
            data_for_visible_state=data_for_visible_state,
            parent_hidden=configuration.is_hidden(component["key"], data),
        )
