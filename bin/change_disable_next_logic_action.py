#!/usr/bin/env python
#
# Change existing "disable next" logic actions into "disable step" logic actions.
#
import sys
from collections.abc import Collection
from pathlib import Path

import django

from tqdm import tqdm

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

# TODO-5861: add console output that some forms require a manual check. Use "click" for
#  this
# TODO-5861: maybe do this in a migration? Not sure if it makes sense to print things to
#  the console in that case though.


def rules_contains_unprocessed_disable_next_action(rules):
    for rule in rules:
        for action in rule.actions:
            if (
                action["action"]["type"] == "disable-next"
                and action["form_step_uuid"] == ""
            ):
                return True

    return False


# TODO-5861: move to Form or openforms.variables.utils? This is also needed for
#  dependency graph
def resolve_key(input_key: str, all_form_variable_keys: Collection[str]) -> str | None:
    """Resolve a JSON logic variable key to its corresponding form variable key."""
    # There is a variable with this exact key, it is a valid reference
    if input_key in all_form_variable_keys:
        return input_key

    # Process nested paths (editgrid, selectboxes, partners, children). Note that this
    # doesn't include other nested fields anymore, e.g. a textfield component with key
    # "foo.bar" will have already been resolved. We process all slices, as these keys
    # could also include dots.
    parts = input_key.split(".")
    for i in range(1, len(parts)):
        if (key := ".".join(parts[:i])) in all_form_variable_keys:
            return key

    # If the outer key also doesn't exist, we cannot resolve the complete key, so we
    # just return `None`. Note that the digest email should notify the user of invalid
    # logic rules
    return None


def create_action(step):
    return {
        "action": {"type": "disable-next"},
        "form_step_uuid": str(step.uuid),
    }


def change_disable_next_logic_action():
    from openforms.forms.models import Form, FormLogic, FormStep, FormVariable
    from openforms.utils.json_logic import introspect_json_logic

    queryset = Form.objects.prefetch_related("formlogic_set", "formvariable_set")
    rules_to_update = set()
    for form in tqdm(
        queryset.iterator(),
        desc="Forms processed",
        total=queryset.count(),
        dynamic_ncols=True,
        mininterval=0.5,
        unit="form",
    ):
        # We don't care about deleted forms
        if form._is_deleted:
            continue

        logic_rules: list[FormLogic] = form.formlogic_set.all()
        # Exit early if none of the rules contain an unprocessed disable action
        if not rules_contains_unprocessed_disable_next_action(logic_rules):
            continue

        # TODO-5861: move to Form? This is also needed for dependency graph
        # Mapping from component to step for quick access
        form_steps = form.formstep_set.select_related("form_definition")
        component_to_step: dict[str, FormStep] = {
            component["key"]: step
            for step in form_steps.iterator()
            for component in step.form_definition.iter_components(
                recursive=True, recurse_into_editgrid=False
            )
        }
        form_variables: dict[str, FormVariable] = {
            var.key: var for var in form.formvariable_set.iterator()
        }

        # Process logic rules
        for rule in logic_rules:
            # Create a set of input variables by analyzing the logic trigger.
            input_variables: set[FormVariable] = set()
            for var in introspect_json_logic(rule.json_logic_trigger).get_input_keys():
                form_variable_key = resolve_key(var.key, form_variables)
                form_variable = form_variables.get(form_variable_key)
                if form_variable is None:
                    continue
                input_variables.add(form_variable)

            for action in rule.actions:
                if action["action"]["type"] != "disable-next":
                    continue
                # elif action["form_step_uuid"] != "":
                #     continue

                rules_to_update.add(rule)

                # Steps of form variables used in the JSON logic trigger. Skip prefilled
                # variables, because they are available upon submission creation
                input_variable_steps = {
                    step
                    for var in input_variables
                    if not var.prefill_plugin
                    if (step := component_to_step.get(var.key)) is not None
                }
                if len(input_variable_steps) == 0:
                    # There are no input variables from the logic trigger, so assign the
                    # first step as a best guess (unless "trigger_from_step" is defined)
                    step_to_assign = (
                        rule.trigger_from_step
                        if rule.trigger_from_step is not None
                        else form_steps.first()
                    )
                    # We have no "trigger_from_step" or variables from the logic
                    # trigger, so assign the first step as a best guess.
                    action["form_step_uuid"] = str(step_to_assign.uuid)
                elif len(input_variable_steps) == 1:
                    # If there is only one, assign the step to it
                    step_to_assign = (
                        rule.trigger_from_step
                        if rule.trigger_from_step is not None
                        else input_variable_steps.pop()
                    )
                    action["form_step_uuid"] = str(step_to_assign.uuid)
                else:
                    # If "trigger_from_step" is defined, ensure we add it, and remove
                    # all other input variable steps that are before it.
                    if rule.trigger_from_step:
                        input_variable_steps.add(rule.trigger_from_step)
                        input_variable_steps = [
                            step
                            for step in input_variable_steps
                            if step.order >= rule.trigger_from_step.order
                        ]

                    # There are multiple steps, so assign the first step to the current
                    # action, and create new actions for the remaining steps
                    input_variable_steps = sorted(
                        input_variable_steps, key=lambda step: step.order
                    )
                    action["form_step_uuid"] = str(input_variable_steps.pop(0).uuid)

                    # Add new actions to the rule
                    new_actions = [create_action(step) for step in input_variable_steps]
                    rule.actions.extend(new_actions)

                # I think it's safe to there is only one "disable next" action per rule
                # TODO-5861: should we double check and remove duplicates?
                break

    if rules_to_update:
        FormLogic.objects.bulk_update(rules_to_update, fields=("actions",))


def main():
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    change_disable_next_logic_action()


if __name__ == "__main__":
    main()
