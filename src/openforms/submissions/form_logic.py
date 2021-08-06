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

    rules = FormLogic.objects.filter(form_step=step.form_step)
    for rule in rules:
        trigger = jsonLogic(rule.json_logic_trigger, data)
        for action in rule.actions:
            if action["type"] == "value":
                configuration = set_property_value(
                    configuration, rule.component, "value", trigger
                )
            elif trigger and action["type"] == "property":
                property_name = action["property"]["value"]
                property_value = action["state"]
                set_property_value(
                    configuration, rule.component, property_name, property_value
                )
            else:
                raise NotImplementedError("This action has not been implemented yet.")

    step._form_logic_evaluated = True

    return configuration
