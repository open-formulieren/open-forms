from typing import TYPE_CHECKING, Any, Dict

from json_logic import jsonLogic

from openforms.formio.utils import get_default_values, get_dynamic_configuration
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormDefinition, FormLogic
from openforms.prefill import JSONObject

if TYPE_CHECKING:  # pragma: nocover
    from .models import Submission, SubmissionStep


def set_property_value(
    configuration: JSONObject,
    component_key: str,
    property_name: str,
    property_value: str,
) -> JSONObject:
    # use :class:`FormDefinition` for the iter_components method
    form_definition = FormDefinition()

    # iter over the (nested) components, and when we find the specified key, mutate it and break
    # out of the loop
    for component in form_definition.iter_components(
        configuration=configuration, recursive=True
    ):
        if component["key"] == component_key:
            component[property_name] = property_value
            break

    return configuration


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
        request=context.get("request"),
        submission=submission,
    )

    # check what the default data values are
    defaults = get_default_values(submission, configuration)

    # merge the default values and supplied data - supplied data overwrites defaults
    # if keys are present in both dicts
    data = {**defaults, **data}

    if not step.data:
        step.data = {}

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return configuration

    rules = FormLogic.objects.filter(form=step.form_step.form)
    submission_state = submission.load_execution_state()

    for rule in rules:
        if jsonLogic(rule.json_logic_trigger, data):
            for action in rule.actions:
                action_details = action["action"]
                if action_details["type"] == LogicActionTypes.value:
                    new_value = jsonLogic(action_details["value"], data)
                    configuration = set_property_value(
                        configuration, action["component"], "value", new_value
                    )
                    step.data[action["component"]] = new_value
                elif action_details["type"] == LogicActionTypes.property:
                    property_name = action_details["property"]["value"]
                    property_value = action_details["state"]
                    set_property_value(
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

    if dirty:
        # only keep the changes in the data, so that old values do not overwrite otherwise
        # debounced client-side data changes
        data_diff = {}
        for key, new_value in step.data.items():
            original_value = data.get(key)
            if new_value == original_value:
                continue
            data_diff[key] = new_value

        # only return the 'overrides'
        step.data = data_diff

    step._form_logic_evaluated = True

    return configuration


def check_submission_logic(submission):
    logic_rules = FormLogic.objects.filter(
        form=submission.form,
        actions__contains=[{"action": {"type": LogicActionTypes.step_not_applicable}}],
    )

    merged_data = submission.data
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
