#!/usr/bin/env python
from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import django

import click
from tabulate import tabulate

if TYPE_CHECKING:
    from openforms.formio.typing import Component

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_component(component: Component) -> str | None:
    match component:
        case {"type": "file", "defaultValue": list() as default_value}:
            if None in default_value:
                return "'null' in file default value"

        case {"type": "licenseplate"}:
            if "validate" not in component:
                return "Missing validation configuration"

        case {"type": "columns", "columns": list() as columns}:
            for col in columns:
                has_problem = False
                if (
                    not (size := col.get("size"))
                    or not isinstance(size, int)
                    or not 1 <= size <= 12
                ):
                    has_problem = True

                if not (size_mobile := col.get("sizeMobile")):
                    if not has_problem:
                        continue

                if not isinstance(size_mobile, int) or not 1 <= size_mobile <= 4:
                    has_problem = True

                if has_problem:
                    return "column (mobile) size is not an integer"

        case {
            "type": "radio",
            "values": list() as values,
            "defaultValue": str() as default_value,
        } if bool(default_value):
            expected_values = [radio_value["value"] for radio_value in values]
            if default_value not in expected_values:
                return f"Default value '{default_value}' is not valid."

        case {
            "type": "textfield" | "textarea",
            "openForms": {"translations": dict() as translations},
        }:
            for translation_dict in translations.values():
                if not isinstance(translation_dict, dict):
                    return "invalid translations structure"
                if bool(translation_dict.get("defaultValue")):
                    return "defaultValue has a translation"


def check_component_html_usage(component: Component) -> list[str]:
    messages = []
    component_properties_to_check = ("label", "description", "tooltip")

    for property_name in component_properties_to_check:
        if property_name not in component:
            continue

        property_value = component[property_name]
        property_contains_html = bool(re.search(r"<\w", property_value))
        if property_contains_html:
            messages.append(f"Component {property_name} contains html: '{property_value}'.")

    return messages


def report_problems(component_types: Sequence[str], check_html_usage: bool) -> bool:
    from openforms.forms.models import FormDefinition

    problems = []

    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        for component in form_definition.iter_components():
            if component_types and component["type"] not in component_types:
                continue

            messages = []
            if check_component_message := check_component(component):
                messages.append(check_component_message)
            if check_html_usage:
                messages.extend(check_component_html_usage(component))

            if len(messages) == 0:
                continue

            problems.append(
                [
                    form_definition.admin_name,
                    component.get("label") or component["key"],
                    component["type"],
                    "\n".join(messages),
                ]
            )

    if not problems:
        click.echo(click.style("No problems found.", fg="green"))
        return True

    click.echo(click.style("Found problems in form definition components.", fg="red"))
    click.echo("")
    click.echo(
        tabulate(
            problems,
            headers=("Form definition", "Component label", "Component type", "Problem"),
        )
    )

    return False


def main(skip_setup=False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_problems(**kwargs)


@click.command()
@click.option("--component-type", multiple=True, help="Limit check to component type.")
@click.option(
    "--include-html-checking",
    is_flag=True,
    default=False,
    help="Include checks for html usage in tooltips, descriptions and labels.",
)
def cli(component_type: Sequence[str], include_html_checking: bool):
    return main(
        component_types=component_type,
        check_html_usage=include_html_checking,
    )


if __name__ == "__main__":
    cli()
