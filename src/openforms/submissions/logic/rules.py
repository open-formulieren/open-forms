from collections.abc import Iterable, Iterator

import elasticapm
from json_logic import jsonLogic

from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
    process_visibility,
)
from openforms.forms.models import FormLogic, FormStep

from ..models import Submission, SubmissionStep
from .actions import ActionOperation
from .log_utils import log_errors


def _include_rule(form_steps: list[FormStep], rule: FormLogic, step_index: int) -> bool:
    # rules that always apply
    if not rule.trigger_from_step:
        return True

    trigger_from_index = form_steps.index(rule.trigger_from_step)
    # if the current step is before the trigger-from step, do not include the rule
    if step_index < trigger_from_index:
        return False

    return True


def get_rules_to_evaluate(
    submission: Submission, current_step: SubmissionStep | None = None
) -> Iterable[FormLogic]:
    """
    Given a submission, return the logic rules ready for evaluation.

    As a side-effect, the form logic query results are cached on ``submission.form``.

    :arg submission: A submission instance to retrieve the rules for
    :arg current_step: The (optional) step at which the rules need to be evaluated. If
      not provided, the step following the last completed step is used, or the first
      step in the form if there are no completed steps.
    :returns: An iterable of :class`openforms.forms.models.FormLogic` instances. This
      may be a queryset, but could also be a list. Typically cached on the form instance
      for performance reasons.
    """
    # some callers evaluate logic for all steps at once, so we can avoid repeated queries
    # by caching the rules on the form instance.
    # Note that form.formlogic_set.all() is never cached by django, so we can't rely
    # on that.
    rules = getattr(submission.form, "_cached_logic_rules", None)
    if rules is None:
        rules = FormLogic.objects.select_related("trigger_from_step").filter(
            form=submission.form
        )
        submission.form._cached_logic_rules = rules

    submission_state = submission.load_execution_state()
    # if there are no form steps, there is no usable form -> there are no logic rules
    # to evaluate
    if not submission_state.form_steps:
        return []

    # filter down the rules that are only applicable in the current step context
    current_step = current_step or get_current_step(submission)
    step_index = (
        submission_state.form_steps.index(current_step.form_step)
        if current_step
        else -1
    )

    return [
        rule
        for rule in rules
        if _include_rule(submission_state.form_steps, rule, step_index)
    ]


def get_current_step(submission: Submission) -> SubmissionStep | None:
    """
    Obtain what the 'current step' of a submission is.

    The current step is defined as the step following the last completed step. Note
    that this does not evaluate any logic, so if this step happens to be made
    not-applicable dynamically, it will still be returned.

    If the last completed step is the last step in the form, then this step is returned.

    :arg submission: The submission instance to get the current step for.
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

    :arg rules: An iterable of form logic rules to evaluate.
    :arg data: Mapping from variable key to variable value (native Python types), for
      all variables present in the :class:`SubmissionValueVariableState`. This data
      structure is updated after every mutation.
    :arg submission: Submission instance.
    :returns: An iterator yielding :class:`ActionOperation` instances.
    """
    state = submission.load_submission_value_variables_state()
    for rule in rules:
        with elasticapm.capture_span(
            "evaluate_rule",
            span_type="app.submissions.logic",
            labels={"ruleId": rule.pk},
        ):
            triggered = False
            with log_errors(rule.json_logic_trigger, rule):
                triggered = bool(jsonLogic(rule.json_logic_trigger, data.data))

            # If the rule was not triggered, we still need to handle the clear on hide,
            # as components can be hidden by default and shown when a logic rule is
            # triggered
            if not triggered:
                _handle_clear_on_hide(rule, data, configuration)
                continue

            for operation in rule.action_operations:
                if mutations := operation.eval(data, configuration, submission):
                    mutations_python = {
                        key: state.variables[key].to_python(value)
                        for key, value in mutations.items()
                    }
                    data.update(mutations_python)

                yield operation


def _handle_clear_on_hide(
    rule: FormLogic, data: FormioData, configuration: FormioConfigurationWrapper
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

        # To avoid doing unnecessary work, only call ``process_visibility`` when the
        # component is actually hidden.
        if not component.get("hidden", False):
            continue

        # Process the visibility of the component. We want to process the component
        # itself, not try to iterate over its children, so we create a 'fake'
        # configuration.
        # Note that we cannot pass ``parent_hidden=True`` here, and skip conditional
        # evaluation (like in ``PropertyAction.eval``), because a component can be
        # affected by a simple conditional which makes it visible.
        process_visibility({"components": [component]}, data, configuration)
