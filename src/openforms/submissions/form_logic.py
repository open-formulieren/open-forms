import copy
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict

import elasticapm
from json_logic import jsonLogic

from openforms.formio.service import get_dynamic_configuration
from openforms.formio.utils import get_component, get_default_values, iter_components
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic
from openforms.logging import logevent
from openforms.prefill import JSONObject

from .models.submission_step import DirtyData

if TYPE_CHECKING:  # pragma: nocover
    from .models import Submission, SubmissionStep


def set_property_value(
    configuration: JSONObject,
    component_key: str,
    property_name: str,
    property_value: str,
) -> JSONObject:
    # iter over the (nested) components, and when we find the specified key, mutate it and break
    # out of the loop
    for component in iter_components(configuration=configuration, recursive=True):
        if component["key"] == component_key:
            component[property_name] = property_value
            break

    return configuration


class DataForLogic:
    """Manage data during logic evaluation

    This class contains the initial data that was passed to the evaluate_form_logic function
    (submission data plus any data entered by the user that hasn't been saved yet).
    It then contains any data added by the logic rules and the static data for this submission.
    """

    initial_data: dict
    _data: dict
    static_data: dict

    def __init__(self, initial_data, static_data):
        self.initial_data = copy.deepcopy(initial_data)
        self.static_data = static_data
        self._data = copy.deepcopy(initial_data)

    def update_data(self, new_data: dict) -> None:
        self._data = {**self.initial_data, **new_data}

    @property
    def data(self) -> dict:
        return {**self._data, **self.static_data}


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
    """
    # grab the configuration that can be **mutated**
    configuration = step.form_step.form_definition.configuration

    # we need to apply the context-specific configurations first before we can apply
    # mutations based on logic, which is then in turn passed to the serializer(s)
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

    # check what the default data values are
    defaults = get_default_values(configuration)

    submission_variables_state = submission.load_submission_value_variables_state()
    static_data = submission_variables_state.static_data(context.get("request"))

    # merge the default values and supplied data - supplied data overwrites defaults
    # if keys are present in both dicts
    data_container = DataForLogic(
        initial_data={**defaults, **data}, static_data=static_data
    )

    if not step.data:
        step.data = DirtyData({})

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return configuration

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

    submission_state = submission.load_execution_state()
    step_index = submission_state.form_steps.index(step.form_step)

    updated_step_data = deepcopy(step.data)
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
        if not trigger_rule:
            continue
        for action in rule.actions:
            action_details = action["action"]
            # TODO this action will be replaced by changing the value of variables
            if action_details["type"] == LogicActionTypes.value:
                new_value = jsonLogic(action_details["value"], data_container.data)
                configuration = set_property_value(
                    configuration, action["component"], "value", new_value
                )
                updated_step_data[action["component"]] = new_value
                data_container.update_data(updated_step_data)
            elif action_details["type"] == LogicActionTypes.property:
                property_name = action_details["property"]["value"]
                property_value = action_details["state"]
                configuration = set_property_value(
                    configuration,
                    action["component"],
                    property_name,
                    property_value,
                )
            elif action_details["type"] == LogicActionTypes.disable_next:
                step._can_submit = False
            elif action_details["type"] == LogicActionTypes.step_not_applicable:
                submission_step_to_modify = submission_state.resolve_step(
                    action["form_step"]
                )
                submission_step_to_modify._is_applicable = False
                # This clears data in the database to make sure that saved steps which later become
                # not-applicable don't have old data
                submission_step_to_modify.data = {}
                if submission_step_to_modify == step:
                    updated_step_data = {}
                    step._is_applicable = False
            elif action_details["type"] == LogicActionTypes.variable:
                new_value = jsonLogic(action_details["value"], data_container.data)
                variable_key = action["variable"]
                updated_step_data[variable_key] = new_value
                data_container.update_data(updated_step_data)
    step.data = DirtyData(updated_step_data)

    # Logging the rules
    logevent.submission_logic_evaluated(
        submission,
        evaluated_rules,
        {**data_container.static_data, **data_container.initial_data},
    )

    if dirty:
        # only keep the changes in the data, so that old values do not overwrite otherwise
        # debounced client-side data changes
        data_diff = {}
        for key, new_value in step.data.items():
            original_value = data_container.initial_data.get(key)
            # Reset the value of any field that may have become hidden again after evaluating the logic
            if original_value:
                component = get_component(configuration, key)
                if (
                    component
                    and component.get("hidden")
                    and component.get("clearOnHide")
                ):
                    data_diff[key] = defaults.get(key, "")
                    continue

            if new_value == original_value:
                continue
            data_diff[key] = new_value

        # only return the 'overrides'
        if data_diff:
            step.data = DirtyData(data_diff)
    step._form_logic_evaluated = True

    return configuration


def check_submission_logic(submission, unsaved_data=None):
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
                if action["action"]["type"] != LogicActionTypes.step_not_applicable:
                    continue

                submission_step_to_modify = submission_state.resolve_step(
                    action["form_step"]
                )
                submission_step_to_modify._is_applicable = False
