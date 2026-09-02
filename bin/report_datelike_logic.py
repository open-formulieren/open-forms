#!/usr/bin/env python
#
# Scan forms for form logic where date/datetime/time components are used and compared
# against the empty value `""`.
#
from __future__ import annotations

import sys
from collections.abc import Collection, Iterator, Mapping
from pathlib import Path
from typing import NamedTuple

import django
from django.db.models import Prefetch

import click
from json_logic.meta import Operation
from json_logic.meta.operations import Var
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


class Row(NamedTuple):
    form_id: int
    form_admin_name: str
    rule_index: int
    variables: Collection[str]


def _test_json_logic_expression(expression, variable_keys: set[str]) -> Iterator[str]:
    from openforms.utils.json_logic import introspect_json_logic
    from openforms.utils.json_logic.datastructures import iter_tree
    from openforms.variables.service import resolve_key

    introspection_result = introspect_json_logic(expression)
    for node, _ in iter_tree(introspection_result.tree, {"in_reduce": False}):
        # only comparison operations against the empty string need to be
        # fixed
        # indirect "date" operator comparisons like below should already be comparing
        # against null:
        #
        # >>> jsonLogic({"==": [{"date": {"var": "myDate"}}, ""]}, {"myDate": ""})
        # False
        #
        # >>> jsonLogic({"==": [{"var": "myDate"}, ""]}, {"myDate": ""})
        # True
        #
        if (
            not isinstance(node, Operation)
            or node.operator not in ("==", "===", "!=", "!==")
            or "" not in node.arguments
        ):
            continue

        for argument in node.arguments:
            if argument == "":
                continue

            if not isinstance(argument, Var):
                continue

            variable = argument.arguments[0]
            if not isinstance(variable, str):
                continue

            # resolve to the relevant variable
            variable = resolve_key(variable, variable_keys)
            if variable is None:
                continue

            yield variable


def report_logic_rules() -> bool:
    """
    Scans and reports the form definitions that might contain unwanted changes
    after performing migrations.

    :returns: ``True`` if no possible unwanted configuration mutations are detected,
    ``False`` if there are issues detected.
    """
    from openforms.forms.constants import LogicActionTypes
    from openforms.forms.models import Form, FormLogic, FormVariable
    from openforms.variables.constants import FormVariableDataTypes
    from openforms.variables.service import get_static_variables

    data_types = (
        FormVariableDataTypes.date,
        FormVariableDataTypes.datetime,
        FormVariableDataTypes.time,
    )

    forms = (
        Form.objects.prefetch_related(
            "formlogic_set",
            Prefetch(
                "formvariable_set",
                queryset=FormVariable.objects.filter(data_type__in=data_types),
                to_attr="variables",
            ),
        )
        .filter(formlogic__isnull=False)
        .distinct()
    )

    relevant_static_variables: set[str] = {
        variable.key
        for variable in get_static_variables()
        if variable.data_type in data_types
    }

    rows: list[Row] = []
    for form in forms.iterator(chunk_size=10):
        variable_keys: set[str] = relevant_static_variables | {
            variable.key for variable in form.variables
        }

        for logic_rule in form.formlogic_set.all():
            # check if the rule uses any of the datelike variables
            variables_to_report: set[str] = set()

            # analyse the trigger for comparison operations
            assert FormLogic.input_variables_from_trigger.fget is not None
            trigger_input_vars: set[str] = FormLogic.input_variables_from_trigger.fget(
                logic_rule
            )
            if variable_keys & trigger_input_vars:
                for key in _test_json_logic_expression(
                    logic_rule.json_logic_trigger, variable_keys
                ):
                    variables_to_report.add(key)

            # analyse the actions for comparison operations
            assert FormLogic.input_variables_from_action_map.fget is not None
            action_input_vars: Mapping[str, set[int]] = (
                FormLogic.input_variables_from_action_map.fget(logic_rule)
            )
            if variable_keys & action_input_vars.keys():
                action_indices_to_check: set[int] = set()
                for key, action_indices in action_input_vars.items():
                    if key not in variable_keys:
                        continue
                    action_indices_to_check |= action_indices

                # only the 'value' actions use json logic expressions
                for index in action_indices_to_check:
                    action = logic_rule.actions[index]
                    if action["action"]["type"] != LogicActionTypes.variable:
                        continue
                    for key in _test_json_logic_expression(
                        action["action"]["value"], variable_keys
                    ):
                        variables_to_report.add(key)

            if variables_to_report:
                rows.append(
                    Row(form.pk, form.admin_name, logic_rule.order, variables_to_report)
                )

    rows.sort(key=lambda row: (row.form_id, row.rule_index))

    if not rows:
        click.echo(click.style("No relevant logic rules found.", fg="green"))
        return True

    click.echo(
        click.style(
            "Found form logic that compares against the empty string.",
            fg="red",
        )
    )
    click.echo("")
    click.echo(
        tabulate(
            rows,
            headers=(
                "Form ID",
                "Form admin name",
                "Logic rule index",
                "Variables used",
            ),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_logic_rules()


if __name__ == "__main__":
    main()
