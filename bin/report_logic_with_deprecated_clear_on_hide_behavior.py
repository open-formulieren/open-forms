#!/usr/bin/env python
# This script detects rules (JSON logic triggers) that compare the value of a variable
# to the related component empty value.
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import django

import click
import msgspec
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
            case {"var": _}, {"var": _}:
                # Cannot determine anything if we have two variable expressions
                return
            case {"var": _}, None | int() | float() | str() | bool():
                # A variable expression + primitive -> possibility of comparing to an
                # empty value
                var_name = JSONLogicExpression.normalize(a)["var"][0]
                # Could be another variable expression, in theory
                if isinstance(var_name, str):
                    yield var_name, b
            case None | int() | float() | str() | bool(), {"var": _}:
                # A primitive + variable expression -> possibility of comparing to an
                # empty value
                var_name = JSONLogicExpression.normalize(b)["var"][0]
                # Could be another variable expression, in theory
                if isinstance(var_name, str):
                    yield var_name, a
            case _:
                # In all other cases, just process the arguments recursively:
                # 1. Variable expression + other expression
                # 2. Two other expressions
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
                    var_name = JSONLogicExpression.normalize(a)["var"][0]
                    # Could be another variable expression, in theory
                    if isinstance(var_name, str):
                        yield var_name, compare_value
            return

    yield from iter_variables_with_compare_value(argument)


def report_rules() -> bool:
    from formio_types import AnyComponent, EditGrid, FormioConfiguration, Selectboxes
    from openforms.formio.registry import register
    from openforms.formio.service import (
        _fixup_component_properties,
        iter_components,
    )
    from openforms.formio.visibility import get_conditional
    from openforms.forms.models import Form, FormLogic
    from openforms.variables.service import resolve_key

    forms_to_check = Form.objects.filter(_is_deleted=False).prefetch_related(
        "formlogic_set", "formstep_set"
    )
    form_with_logic_with_risk: defaultdict[tuple[Form, FormLogic], set[str]] = (
        defaultdict(set)
    )
    for form in forms_to_check.iterator(chunk_size=10):
        components_with_affected_visibility: set[str] = set()

        # Mapping from component to step for quick access
        form_steps = form.formstep_set.select_related("form_definition")
        component_map: dict[str, AnyComponent] = {}
        for form_step in form_steps:
            formio_configuration = msgspec.convert(
                form_step.form_definition.configuration,
                type=FormioConfiguration,
                dec_hook=_fixup_component_properties,
            )
            for component in iter_components(
                formio_configuration,
                recursive=True,
                recurse_into_editgrid=False,
            ):
                component_map[component.key] = component

                # Component with visibility affected by a conditional
                if get_conditional(component) is not None:
                    components_with_affected_visibility.add(component.key)

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
                child.key
                for child in iter_components(
                    component, recursive=True, recurse_into_editgrid=False
                )
            }
            components_with_affected_visibility.update(children)

        for rule in form.formlogic_set.iterator():
            for var_name, comp_value in iter_variables_with_compare_value(
                rule.json_logic_trigger
            ):
                if (resolved_key := resolve_key(var_name, component_map)) is None:
                    # Variable cannot be resolved, so we cannot determine anything
                    continue

                component = component_map[resolved_key]
                if isinstance(component, EditGrid) and var_name != resolved_key:
                    # We expect data access "editgrid.x.child_key" here, so discard the
                    # parent key and index. Assuming there are no nested editgrids here
                    # :see_no_evil:
                    _, child_key = var_name.removeprefix(f"{resolved_key}.").split(
                        ".", 1
                    )

                    children_map: dict[str, AnyComponent] = {
                        child.key: child
                        for child in iter_components(
                            component, recursive=True, recurse_into_editgrid=False
                        )
                    }
                    resolved_key = resolve_key(child_key, children_map)
                    assert resolved_key is not None
                    component = children_map[resolved_key]

                # Visibility of component is not affected and/or component does not have
                # clearOnHide enabled, so it's not relevant
                if (
                    resolved_key not in components_with_affected_visibility
                    or not getattr(component, "clear_on_hide", True)
                ):
                    continue

                empty_value = register.get_empty_value(component)
                if isinstance(component, Selectboxes):
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
                # at the moment, but there is no such guarantee for nested data.
                if comp_value in [empty_value, None, component.default_value]:
                    form_with_logic_with_risk[form, rule].add(var_name)

    data = [
        (form.admin_name, form.pk, rule.order, ", ".join(var_names))
        for (form, rule), var_names in form_with_logic_with_risk.items()
    ]
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
                    "Variable names in logic trigger",
                ),
            )
        )
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
