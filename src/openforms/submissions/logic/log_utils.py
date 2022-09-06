from typing import Dict, List

from openforms.forms.models import FormLogic, FormVariable

from .actions import compile_action_operation


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
