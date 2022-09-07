import contextlib
import logging
from typing import Any, Dict, List

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


@contextlib.contextmanager
def log_errors(logic: JSONObject, rule: FormLogic) -> Any:
    try:
        yield
    except Exception as error:
        logger.error(
            "Error in rule %s: evaluation of %s failed.", rule.pk, logic, exc_info=error
        )
        logevent.logic_evaluation_failed(rule, error, logic)
