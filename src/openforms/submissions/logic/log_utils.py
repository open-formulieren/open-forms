import logging
from typing import Any, Dict, List

from json_logic import jsonLogic

from openforms.forms.models import FormLogic, FormVariable
from openforms.logging import logevent
from openforms.typing import JSONObject

from .actions import compile_action_operation

logger = logging.getLogger(__name__)


def get_targeted_components(
    rule: FormLogic,
    components_map: dict,
    all_variables: Dict[str, FormVariable],
    initial_data: dict,
) -> List[dict]:
    targeted_components = []
    for action in rule.actions:
        action_operation = compile_action_operation(action)
        action_log_data = action_operation.get_action_log_data(
            component_map=components_map,
            all_variables=all_variables,
            initial_data=initial_data,
        )
        targeted_components.append(action_log_data)

    return targeted_components


def evaluate_json_logic(logic: JSONObject, data: dict, rule: FormLogic) -> Any:
    try:
        return jsonLogic(logic, data)
    except Exception as error:
        logger.error(
            "Error in rule %s: evaluation of %s raised error: %s", rule.pk, logic, error
        )
        logevent.logic_evaluation_failed(rule, error, logic)
