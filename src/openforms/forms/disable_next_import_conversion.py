import uuid
from collections.abc import Mapping
from uuid import UUID

from django.db.models import prefetch_related_objects

from openforms.formio.service import iter_components
from openforms.forms.models import FormStep, FormVariable
from openforms.typing import JSONObject
from openforms.utils.json_logic import introspect_json_logic
from openforms.variables.service import resolve_key


def create_action(step):
    return {
        "action": {"type": "disable-next"},
        "form_step_uuid": str(step.uuid),
        "uuid": str(uuid.uuid4()),
    }


def rule_contains_disable_next_action(rule):
    for action in rule["actions"]:
        if action["action"]["type"] == "disable-next":
            return True

    return False


def add_form_step_uuid_to_disable_next_actions(
    rule: JSONObject,
    form_variables: Mapping[str, FormVariable],
    form_step_map: Mapping[UUID, FormStep],
):
    if not rule_contains_disable_next_action(rule):
        return

    if not form_step_map:  # pragma: nocover
        # Unlikely that a form without steps will be imported, but this avoids a hard
        # crash.
        return

    # Mapping from component to step for quick access
    form_step_list = list(form_step_map.values())
    prefetch_related_objects(form_step_list, "form_definition")
    component_to_step = {
        component["key"]: step
        for step in form_step_list
        for component in iter_components(
            step.form_definition.configuration,
            recursive=True,
            recurse_into_editgrid=False,
        )
    }

    # Process logic rule
    # Create a set of input variable steps by analyzing the logic trigger.
    input_variable_steps = set()
    first_step = form_step_list[0]
    for input_var in introspect_json_logic(rule["json_logic_trigger"]).get_input_keys():
        form_variable_key = resolve_key(input_var.key, form_variables)
        if (
            form_variable := form_variables.get(form_variable_key)
        ) is None:  # pragma: nocover
            continue

        if form_variable.prefill_plugin:
            # If the variable has prefill configured -> add the first step.
            # This is because prefilled data will be available upon submission
            # creation, so the rule _could_ be triggered on the first step. If
            # prefill did not succeed, we still need to execute it on step of
            # the input variable as well, because the user might be asked to
            # fill in the data manually.
            input_variable_steps.add(first_step)

        if (step := component_to_step.get(form_variable.key)) is None:
            # Cannot resolve step -> do nothing (likely because the variable is
            # user defined).
            continue

        input_variable_steps.add(step)

    trigger_from_step = rule.get("trigger_from_step")
    if trigger_from_step is not None:
        assert isinstance(trigger_from_step, str)
        # This is dirty, but we cannot get the instance from the serializer without
        # validating it first, which is not possible without adjusting the disable-next
        # actions :upside_down_face:
        step_uuid = trigger_from_step.rsplit("/", 1)[1]
        # Note that the step UUID should exist in the form step map, because they are
        # replaced from a UUID map in `import_form_data`. If it doesn't, the
        # configuration is broken, but a `.get` avoids a hard crash.
        trigger_from_step = form_step_map.get(UUID(step_uuid))

    new_actions = []
    for action in rule["actions"]:
        new_actions.append(action)

        if action["action"]["type"] != "disable-next" or action.get("form_step_uuid"):
            # Skip non disable-next actions, or if a form step uuid was already
            # configured -> trust it to be correct, to avoid (possibly incorrectly)
            # overwriting it.
            continue

        if len(input_variable_steps) == 0:
            # There are no input variables from the logic trigger, so assign the
            # first step as a best guess (unless "trigger_from_step" is
            # defined).
            step_to_assign = (
                trigger_from_step if trigger_from_step is not None else first_step
            )
            action["form_step_uuid"] = str(step_to_assign.uuid)
        elif len(input_variable_steps) == 1:
            # If there is only one step, assign it to the action (unless
            # "trigger_from_step" is defined).
            step_to_assign = (
                trigger_from_step
                if trigger_from_step is not None
                else input_variable_steps.pop()
            )
            action["form_step_uuid"] = str(step_to_assign.uuid)
        else:
            # If "trigger_from_step" is defined, ensure we add it, and remove
            # all other input variable steps that are before it.
            if trigger_from_step:
                input_variable_steps.add(trigger_from_step)
                input_variable_steps = [
                    step
                    for step in input_variable_steps
                    if step.order >= trigger_from_step.order
                ]

            # There are multiple steps, so assign the first step to the current
            # action, and create new actions for the remaining steps
            input_variable_steps = sorted(
                input_variable_steps, key=lambda step: step.order
            )
            action["form_step_uuid"] = str(input_variable_steps.pop(0).uuid)

            # Add new actions to the rule
            new_actions.extend([create_action(step) for step in input_variable_steps])

    rule["actions"] = new_actions
