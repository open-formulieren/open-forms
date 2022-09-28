"""
Process the logic evaluation logging information.

This relies on the datastructures used in :mod:`openforms.submissions.form_logic`.
"""
from typing import List

from openforms.submissions.logic.log_utils import get_targeted_components
from openforms.submissions.logic.rules import EvaluatedRule
from openforms.submissions.models import Submission
from openforms.typing import JSONObject
from openforms.utils.json_logic import ComponentMeta, introspect_json_logic

from .logevent import _create_log


def log_logic_evaluation(
    submission: Submission,
    evaluated_rules: List["EvaluatedRule"],
    initial_data: JSONObject,
    resolved_data: JSONObject,
):
    if not evaluated_rules:
        return
    evaluated_rules_list = []

    submission_state = submission.load_execution_state()
    form_steps = submission_state.form_steps

    # Keep a mapping for each component's key for each component in the entire form.
    # The key of the mapping is the component key, the value is a dataclass composed of
    # form_step and component definition
    components_map = {}
    for form_step in form_steps:
        for component in form_step.form_definition.iter_components():
            components_map[component["key"]] = ComponentMeta(form_step, component)

    input_data = []
    all_variables = submission.form.formvariable_set.distinct("key").in_bulk(
        field_name="key"
    )
    for evaluated_rule in evaluated_rules:
        rule = evaluated_rule.rule

        trigger = rule.json_logic_trigger
        if not isinstance(trigger, (dict, list)):
            # The trigger was a primitive, no need to introspect
            evaluated_rule_data = {
                "raw_logic_expression": trigger,
                "readable_rule": str(trigger),
                "targeted_components": get_targeted_components(
                    rule,
                    components_map,
                    all_variables,
                    initial_data,
                ),
                "trigger": evaluated_rule.triggered,
            }

            evaluated_rules_list.append(evaluated_rule_data)
            continue

        rule_introspection = introspect_json_logic(
            trigger, components_map, initial_data
        )

        # Gathering all the input component of each evaluated rule
        input_data.extend(rule_introspection.get_input_components())

        targeted_components = get_targeted_components(
            rule, components_map, all_variables, initial_data
        )
        evaluated_rule_data = {
            "raw_logic_expression": rule_introspection.expression,
            "readable_rule": rule_introspection.as_string(),
            "targeted_components": targeted_components,
            "trigger": evaluated_rule.triggered,
        }

        evaluated_rules_list.append(evaluated_rule_data)

    # de-duplication of input data
    deduplicated_input_data = {node["key"]: node for node in input_data}

    return _create_log(
        submission,
        "submission_logic_evaluated",
        extra_data={
            "evaluated_rules": evaluated_rules_list,
            "input_data": deduplicated_input_data,
            "resolved_data": resolved_data,
        },
    )
