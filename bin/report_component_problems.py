#!/usr/bin/env python
from __future__ import annotations

import re
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import django
from django.utils.text import Truncator

import click
from tabulate import tabulate

if TYPE_CHECKING:
    from openforms.formio.typing import Component

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_component(component: Component) -> Iterator[str]:
    from rest_framework.exceptions import ValidationError

    from openforms.api.geojson import GeoJsonGeometryPolymorphicSerializer

    match component:
        case {"conditional": {"show": ""} | {"when": ""}}:
            yield "Unexpected empty strings in conditional."

    match component:
        case {"errors": dict() as errors_dict} if len(errors_dict.keys()):
            yield "Unexpected non-empty component.errors."

    match component:
        case {"openForms": {"dataSrc": "variable", "itemsExpression": str()}}:
            yield "String itemsExpression instead of JSON Logic expression."

    match component:
        case {"type": "radio" | "selectboxes", "values": list() as values} if (
            len(values) == 1
        ):
            if values[0]["value"] == "" and values[0]["label"] == "":
                yield "A single option with blank label is present."
        case {"type": "select", "data": {"values": list() as values}} if (
            len(values) == 1
        ):
            if values[0]["value"] == "" and values[0]["label"] == "":
                yield "A single option with blank label is present."

    match component:
        case {"type": "file", "defaultValue": list() as default_value}:
            if None in default_value:
                yield "'null' in file default value"

        case {"type": "licenseplate"}:
            if "validate" not in component:
                yield "Missing validation configuration"

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
                    yield "column (mobile) size is not an integer"

        case {
            "type": "radio",
            "values": list() as values,
            "defaultValue": str() as default_value,
        } if bool(default_value):
            expected_values = [radio_value["value"] for radio_value in values]
            if default_value not in expected_values:
                yield f"Default value '{default_value}' is not valid."

        case {"type": "radio" | "select"} if component.get("defaultValue") is None:
            yield "'null' default value."

        case {
            "type": "textfield" | "textarea",
            "openForms": {"translations": dict() as translations},
        }:
            for translation_dict in translations.values():
                if not isinstance(translation_dict, dict):
                    yield "invalid translations structure"
                if bool(translation_dict.get("defaultValue")):
                    yield "defaultValue has a translation"

        case {"type": "map"}:
            default_value = component.get("defaultValue")
            if default_value is None:
                # No defaultValue is a-okay
                return

            try:
                if isinstance(
                    default_value, dict
                ) and GeoJsonGeometryPolymorphicSerializer(data=default_value).is_valid(
                    raise_exception=True
                ):
                    # This object has a valid Geometry shape
                    return None
            except ValidationError as error:
                yield f"Default value '{default_value}' is not valid.\nError: {error.detail}"

            # Any other value is automatically invalid
            yield f"Default value '{default_value}' is not valid."

        case {"type": "date"}:
            validate = component.get("validate", {})
            date_picker = component.get("datePicker", {})

            min_date = validate.get("minDate")
            if min_date == "":
                yield "validate.minDate is empty string instead of null."
            if min_date and "T" in min_date:
                yield "validate.minDate is a datetime rather than date."

            max_date = validate.get("maxDate")
            if max_date == "":
                yield "validate.maxDate is empty string instead of null."
            if max_date and "T" in max_date:
                yield "validate.maxDate is a datetime rather than date."

            dp_min_date = date_picker.get("minDate")
            if dp_min_date == "":
                yield "datePicker.minDate is empty string instead of null."
            dp_max_date = date_picker.get("maxDate")
            if dp_max_date == "":
                yield "datePicker.maxDate is empty string instead of null."

            if date_picker["initDate"] != "":
                yield "datePicker.initDate is not empty string."

        case {"type": "datetime"}:
            validate = component.get("validate", {})
            date_picker = component.get("datePicker", {})

            min_datetime = validate.get("minDate")
            if min_datetime == "":
                yield "validate.minDate is empty string instead of null."

            max_datetime = validate.get("maxDate")
            if max_datetime == "":
                yield "validate.maxDate is empty string instead of null."

            dp_min_date = date_picker.get("minDate")
            if dp_min_date == "":
                yield "datePicker.minDate is empty string instead of null."
            if dp_min_date and 11 <= len(dp_min_date) <= 16:
                yield "datePicker.minDate is not a valid RFC3339 encoded datetime."

            dp_max_date = date_picker.get("maxDate")
            if dp_max_date == "":
                yield "datePicker.maxDate is empty string instead of null."
            if dp_max_date and 11 <= len(dp_max_date) <= 16:
                yield "datePicker.maxDate is not a valid RFC3339 encoded datetime."

            if date_picker["initDate"] != "":
                yield "datePicker.initDate is not empty string."

        case {"type": "time"}:
            validate = component.get("validate", {})
            min_time = validate.get("minTime")
            if min_time == "":
                yield "validate.minTime is empty string instead of null."
            max_time = validate.get("maxTime")
            if max_time == "":
                yield "validate.maxTime is empty string instead of null."

        case {"type": "bsn" | "postcode"}:
            if "defaultValue" in component and component["defaultValue"] is None:
                yield "Unexpected None defaultValue."

        case {"type": "checkbox" | "email" | "radio" | "select"}:
            if "translatedErrors" in component:
                for language_code, errors in component["translatedErrors"].items():
                    if (keys := set(errors.keys())) != {"required"}:
                        yield (
                            f"Unexpected error keys {keys - {'required'}} for lang "
                            f"{language_code}."
                        )


def check_component_html_usage(component: Component) -> list[str]:
    messages = []
    component_properties_to_check = ("label", "description", "tooltip")

    for property_name in component_properties_to_check:
        if property_name not in component:
            continue

        property_value = component[property_name]
        property_contains_html = bool(re.search(r"<\w", property_value))
        if property_contains_html:
            messages.append(
                f"Component {property_name} contains html: '{property_value}'."
            )

    return messages


def report_problems(component_types: Sequence[str], check_html_usage: bool) -> bool:
    from openforms.forms.models import FormDefinition

    problems = []

    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        for component in form_definition.iter_components():
            if component_types and component["type"] not in component_types:
                continue

            messages = [msg for msg in check_component(component)]
            if check_html_usage:
                messages.extend(check_component_html_usage(component))

            if len(messages) == 0:
                continue

            label = component.get("label") or component["key"]
            problems.append(
                [
                    form_definition.admin_name,
                    form_definition.pk,
                    Truncator(label).chars(40),
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
            headers=(
                "Form definition",
                "ID",
                "Component label",
                "Component type",
                "Problem",
            ),
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
