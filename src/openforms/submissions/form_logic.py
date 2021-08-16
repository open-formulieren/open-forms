from typing import Any, Dict

from json_logic import jsonLogic

from ..forms.models.form import FormLogic
from ..prefill import JSONObject
from .models import SubmissionStep


def set_property_value(
    configuration: JSONObject,
    component_key: str,
    property_name: str,
    property_value: str,
) -> JSONObject:
    for index, component in enumerate(configuration["components"]):
        if "components" in component:
            configuration = set_property_value(
                component, component_key, property_name, property_value
            )

        if component["key"] == component_key:
            configuration["components"][index][property_name] = property_value

    return configuration


def evaluate_form_logic(step: SubmissionStep, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all the form logic rules and mutate the step configuration if required.
    """
    # grab the configuration that can be **mutated**
    configuration = step.form_step.form_definition.configuration

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return configuration

    rules = FormLogic.objects.filter(form=step.form_step.form)
    for rule in rules:
        if jsonLogic(rule.json_logic_trigger, data):
            for action in rule.actions:
                action_details = action["action"]
                if action_details["type"] == "value":
                    new_value = jsonLogic(action_details["value"], data)
                    configuration = set_property_value(
                        configuration, action["component"], "value", new_value
                    )
                elif action_details["type"] == "property":
                    property_name = action_details["property"]["value"]
                    property_value = action_details["state"]
                    set_property_value(
                        configuration,
                        action["component"],
                        property_name,
                        property_value,
                    )
                elif action_details["type"] == "disable-next":
                    step._can_submit = False

    step._form_logic_evaluated = True

    return configuration
