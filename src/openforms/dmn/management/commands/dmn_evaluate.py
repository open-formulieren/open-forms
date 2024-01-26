import argparse
import builtins
from typing import Any

from django.core.management import BaseCommand

from tabulate import tabulate

from ...registry import register
from ...service import evaluate_dmn


def input_variable(input_string: str) -> tuple[str, Any]:
    bits = input_string.split("::")
    if len(bits) == 2:
        bits = [bits[0], "str", bits[1]]
    elif len(bits) != 3:
        raise ValueError(
            "A single variable must be in the format 'name::type::value' or 'name::value'"
        )

    name, cast_function_name, raw_value = bits

    cast_function = getattr(builtins, cast_function_name, None)
    if cast_function is None or not callable(cast_function):
        raise ValueError(f"The cast funtion '{cast_function}' is not valid.")

    value = cast_function(raw_value)
    return (name, value)


class Command(BaseCommand):
    help = "Execute a decision definition evaluation"

    def add_arguments(self, parser) -> None:
        engines = [plugin.identifier for plugin in register.iter_enabled_plugins()]
        parser.add_argument(
            "definition_id", help="ID of the decision definition to evaluate"
        )
        parser.add_argument(
            "--engine",
            required=len(engines) != 1,
            choices=engines,
            default=engines[0] if len(engines) == 1 else argparse.SUPPRESS,
            help="The engine/plugin to use for evaluation",
        )
        parser.add_argument(
            "--definition-version",
            default="",
            help=(
                "Optional definition version to evaluate. If not specified, the latest "
                "version should be used."
            ),
        )
        parser.add_argument(
            "--vars",
            nargs="*",
            type=input_variable,
            help=(
                "A space separate list of <varname>::<vartype>::<value> input variables. "
                "The type should be a python type. If not specified, 'str' is assumed."
            ),
        )

    def handle(self, **options):
        engine = options["engine"]
        definition_id = options["definition_id"]
        version = options["definition_version"]
        variables = options["vars"] or ()

        result = evaluate_dmn(
            engine, definition_id, version=version, input_values=dict(variables)
        )

        input_vars_table = tabulate(
            [[name, value, type(value)] for name, value in variables],
            headers=["Name", "Value", "Type"],
        )
        self.stdout.write("Input:\n\n")
        for line in input_vars_table.splitlines():
            self.stdout.write(f"  {line}")

        if not result:
            self.stdout.write("No output variables.")
        else:
            self.stdout.write("\nOutput:\n\n")
            table = tabulate(
                [[name, value, type(value)] for name, value in result.items()],
                headers=["Name", "Value", "Type"],
            )
            for line in table.splitlines():
                self.stdout.write(f"  {line}")
