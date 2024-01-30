import contextlib
import logging
from typing import Any

from openforms.forms.models import FormLogic, FormVariable
from openforms.typing import JSONObject, JSONValue

logger = logging.getLogger(__name__)


def get_targeted_components(
    rule: FormLogic,
    components_map: dict,
    all_variables: dict[str, FormVariable],
    initial_data: dict,
    action_log_data: dict[int, JSONValue],
) -> list[dict]:
    return [
        action_operation.get_action_log_data(
            component_map=components_map,
            all_variables=all_variables,
            initial_data=initial_data,
            log_data=action_log_data.get(str(i), {}),  # XXX who str'd my int?
        )
        for i, action_operation in enumerate(rule.action_operations)
    ]


@contextlib.contextmanager
def log_errors(logic: JSONObject, rule: FormLogic) -> Any:
    try:
        yield
    except Exception as error:
        logger.error(
            "Error in rule %s: evaluation of %s failed.", rule.pk, logic, exc_info=error
        )
