#!/usr/bin/env python
# This script detects rules (JSON logic triggers) that compare the value of a variable
# to the related component empty value.
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import django

import click
from json_logic.meta import JSONLogicExpression
from json_logic.meta.expressions import destructure
from json_logic.typing import JSON
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def iter_variables_with_compare_value(expression: JSON):
    if isinstance(expression, list):
        for expr in expression:
            yield from iter_variables_with_compare_value(expr)

    if not isinstance(expression, dict):
        # We have reached a primitive, so there's nothing to do
        return

    normalized = JSONLogicExpression.normalize(expression)
    assert isinstance(normalized, dict)
    operator, argument = destructure(normalized)

    # I think using `>`, `>=`, `<`, and `<=` to perform comparisons with empty
    # containers and strings seems like a SUPER RARE, ULTRA DIRTY edge case that we can
    # leave out here :sweat_smile: Let those rules break and force form designers to
    # rewrite them
    if operator in ["==", "!=", "===", "!=="]:
        a, b = argument
        match a, b:
            case {"var": _}, None | int() | float() | str() | bool():
                # A variable expression + primitive -> possibility of comparing to an
                # empty value
                var_name, *default = JSONLogicExpression.normalize(a)["var"]
                if default:
                    # No need to report expressions that already have a default value
                    return
                # Could be another variable expression, in theory
                if isinstance(var_name, str):
                    yield var_name, b
            case None | int() | float() | str() | bool(), {"var": _}:
                # A primitive + variable expression -> possibility of comparing to an
                # empty value
                var_name, *default = JSONLogicExpression.normalize(b)["var"]
                if default:
                    # No need to report expressions that already have a default value
                    return
                # Could be another variable expression, in theory
                if isinstance(var_name, str):
                    yield var_name, a
            case _:
                # In all other cases, just process the arguments recursively:
                # 1. Two variable expressions
                # 2. Variable expression + other expression
                # 3. Two other expressions
                yield from iter_variables_with_compare_value(argument)
        return
    elif operator == "in":
        a, b = argument
        if isinstance(a, dict) and "var" in a and isinstance(b, list):
            for compare_value in b:
                if isinstance(compare_value, dict | list):
                    # Unlikely, but recurse into these containers to uncover nested
                    # variable expressions
                    yield from iter_variables_with_compare_value(compare_value)
                else:
                    # If x is a primitive, we can yield it together with the variable
                    # name
                    var_name, *default = JSONLogicExpression.normalize(a)["var"]
                    if default:
                        # No need to report expressions that already have a default value
                        return
                    # Could be another variable expression, in theory
                    if isinstance(var_name, str):
                        yield var_name, compare_value
            return
    elif operator == "var" and len(argument) == 1:
        # Individual variable expressions can be reported if they don't have a default
        # (ignoring nested expressions)
        if isinstance(argument[0], str):
            yield argument[0], None

    yield from iter_variables_with_compare_value(argument)


def analyze_rule(
    *,
    rule,
    form,
    component_map,
    components_with_affected_visibility,
    data,
):
    from openforms.formio.service import (
        get_component_empty_value,
        iter_components,
    )
    from openforms.formio.typing import Component
    from openforms.submissions.logic.actions import (
        EvaluateDMNAction,
        ServiceFetchAction,
        VariableAction,
    )
    from openforms.variables.service import resolve_key

    first_execution_step = (
        min(rule.steps, key=lambda step: step.order) if rule.steps else None
    )

    def analyze_json_logic(json_logic_expression):
        variable_names_clearonhide = set()
        variable_names_future_steps = set()
        for var_name, comp_value in iter_variables_with_compare_value(
            json_logic_expression
        ):
            if (resolved_key := resolve_key(var_name, component_map)) is None:
                # Variable cannot be resolved, so we cannot determine anything
                continue

            variable_step = form.get_form_step(resolved_key)
            component = component_map[resolved_key]
            if component["type"] == "editgrid" and var_name != resolved_key:
                key_list = var_name.removeprefix(f"{resolved_key}.").split(".", 1)
                if len(key_list) == 2:
                    # We expect data access "editgrid.x.child_key" here, so discard the
                    # parent key and index. Assuming there are no nested editgrids here
                    # :see_no_evil:
                    children_map: dict[str, Component] = {
                        child["key"]: child
                        for child in iter_components(
                            component, recursive=True, recurse_into_editgrid=False
                        )
                    }
                    resolved_key = resolve_key(key_list[1], children_map)
                    assert resolved_key is not None
                    component = children_map[resolved_key]
                else:
                    # Data access key was "editgrid.x" - we can't do anything in that
                    # case
                    continue

            empty_value = get_component_empty_value(component)
            if component["type"] == "selectboxes":
                # `get_component_empty_value` returns {"option_a": False, "option_b": False, etc...}
                # for a selectboxes component, which is not a useful in this
                # context. It is not possible to use a dictionary as a comparison
                # value in a logic trigger, because it will be interpreted as an
                # expression itself. This means data access always happens using
                # "selectboxes.option_a", and we should just default to the
                # individual empty value.
                empty_value = False

            # The comparison value `None` will also no longer work, as it's the
            # current default that is set when a variable is missing from the
            # context. Note that all form variables should be present in the context
            # at the moment, but there is no such guarantee for nested data. If the
            # compare value is anything else (for example, one of the options of a radio
            # component) we don't have to report it, because the expression can only
            # trigger once the component is actually filled in -> no change w.r.t.
            # current behaviour.
            if comp_value not in [empty_value, None, component.get("defaultValue")]:
                continue

            if resolved_key in components_with_affected_visibility and component.get(
                "clearOnHide", True
            ):
                variable_names_clearonhide.add(var_name)

            if (
                variable_step
                and first_execution_step
                and first_execution_step.order < variable_step.order
            ):
                variable_names_future_steps.add(var_name)

        return variable_names_clearonhide, variable_names_future_steps

    ##########################
    ### JSON LOGIC TRIGGER ###
    ##########################
    vars_clearonhide, vars_future_steps = analyze_json_logic(rule.json_logic_trigger)
    if vars_clearonhide:
        data.append(
            (
                form.admin_name,
                form.pk,
                rule.order,
                ", ".join(vars_clearonhide),
                "clear on hide behavior (trigger)",
            )
        )
    if vars_future_steps:
        data.append(
            (
                form.admin_name,
                form.pk,
                rule.order,
                ", ".join(vars_future_steps),
                "variables from future steps (trigger)",
            )
        )

    ###############
    ### ACTIONS ###
    ###############
    for action in rule.action_operations:
        if isinstance(action, VariableAction):
            vars_clearonhide, vars_future_steps = analyze_json_logic(action.value)
            if vars_clearonhide:
                data.append(
                    (
                        form.admin_name,
                        form.pk,
                        rule.order,
                        ", ".join(vars_clearonhide),
                        "clear on hide behavior (variable action)",
                    )
                )
            if vars_future_steps:
                data.append(
                    (
                        form.admin_name,
                        form.pk,
                        rule.order,
                        ", ".join(vars_future_steps),
                        "variables from future steps (variable action)",
                    )
                )

        # Note: variables from service fetch settings are extracted from templates, so
        # we can't check whether form designers have fixed their implementations.
        # Note: it is not possible to add defaults for variables used in DMN actions, so
        # we can only report that they are used.
        elif isinstance(action, ServiceFetchAction | EvaluateDMNAction):
            resolved_keys = {
                resolved_key
                for key in action.unresolved_input_variables
                if (resolved_key := resolve_key(key, component_map))
            }
            vars_clearonhide = components_with_affected_visibility & resolved_keys
            vars_future_steps = {
                key
                for key in resolved_keys
                if first_execution_step
                and (step := form.get_form_step(key))
                and first_execution_step.order < step.order
            }
            if variable_names := vars_clearonhide | vars_future_steps:
                data.append(
                    (
                        form.admin_name,
                        form.pk,
                        rule.order,
                        ", ".join(variable_names),
                        f"used in {action.__class__.__name__} but may be missing",
                    )
                )


def report_rules() -> bool:
    from openforms.formio.service import iter_components
    from openforms.formio.typing import Component
    from openforms.formio.visibility import get_conditional
    from openforms.forms.models import Form

    forms_to_check = Form.objects.filter(_is_deleted=False).prefetch_related(
        "formlogic_set", "formstep_set"
    )
    data = []
    errors = []
    for form in forms_to_check.iterator(chunk_size=10):
        components_with_affected_visibility: set[str] = set()

        # Mapping from component to step for quick access
        form_steps = form.formstep_set.select_related("form_definition")
        component_map: dict[str, Component] = {}
        for form_step in form_steps:
            for component in iter_components(
                form_step.form_definition.configuration,
                recursive=True,
                recurse_into_editgrid=False,
            ):
                component_map[component["key"]] = component

                # Component with visibility affected by a conditional
                if get_conditional(component) is not None:
                    components_with_affected_visibility.add(component["key"])

        # Components with visibility affected by logic rules
        for rule in form.formlogic_set.iterator():
            components_with_affected_visibility |= rule.components_in_hidden_actions

        # Add children of all components that have their visibility affected. Create
        # a copy to avoid processing children again, as the set is updated directly
        for key in components_with_affected_visibility.copy():
            # Take into account invalid logic rules
            if key not in component_map:
                continue

            component = component_map[key]
            children = {
                child["key"]
                for child in iter_components(
                    component, recursive=True, recurse_into_editgrid=False
                )
            }
            components_with_affected_visibility.update(children)

        for rule in form.formlogic_set.iterator():
            try:
                analyze_rule(
                    rule=rule,
                    form=form,
                    component_map=component_map,
                    components_with_affected_visibility=components_with_affected_visibility,
                    data=data,
                )
            except Exception:
                errors.append(
                    (form.admin_name, form.pk, rule.order, traceback.format_exc())
                )

    if data:
        click.echo(
            click.style(
                "Found logic rules with a risk of behaving differently in Open Forms "
                "4.0",
                fg="red",
            )
        )
        click.echo("")
        click.echo(
            tabulate(
                data,
                headers=(
                    "Form admin name",
                    "Form ID",
                    "Logic rule number",
                    "Variable names",
                    "Reason",
                ),
            )
        )
        click.echo("")
    if errors:
        click.echo(click.style("Logic rules with errors during analysis", fg="red"))
        click.echo("")
        click.echo(
            tabulate(
                errors,
                headers=(
                    "Form admin name",
                    "Form ID",
                    "Logic rule number",
                    "Error",
                ),
            )
        )

    if errors or data:
        return False
    else:
        click.echo(
            click.style(
                "No logic rules with a risk of behaving differently in Open Forms 4.0",
                fg="green",
            )
        )
        return True


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_rules()


if __name__ == "__main__":
    main()
