#!/usr/bin/env python
#
# Scans form definitions that might contain unwanted changes after performing
# migrations. b3c9c17b4b0d024c886301220b4fc0f04c51919f introduced changes that
# were too strict as it removed `eq` values whenever other conditional properties
# where falsy, while the intend was that the removal should've only happened
# whenever the properties values were null or whenever all (known) properties
# were not present at all.
#
# This check is intended to run *after* the data migrations that applied fixes
# to the component configurations. It cannot be run in a preventive manner as
# upgrade check because these problems cannot be corrected pre-3.5.
#
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

import django
from django.db.models import Prefetch

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


class Row(NamedTuple):
    form_definition_id: int
    form_definition_name: str
    component_keys: set[str]
    form_steps: set[str]
    form_admin_name: str
    form_id: int


class Empty:
    def __bool__(self):
        return False


empty = Empty()


def report_configurations() -> bool:
    """
    Scans and reports the form definitions that might contain unwanted changes
    after performing migrations.

    :returns: ``True`` if no possible unwanted configuration mutations are detected,
    ``False`` if there are issues detected.
    """
    from openforms.forms.models import Form, FormDefinition, FormStep

    # fmt:off
    form_definitions = (
        FormDefinition.objects.prefetch_related(
            Prefetch(
                "formstep_set",
                queryset=FormStep.objects.select_related("form"),
            ),
        )
        .filter(_num_components__gte=1)
    )
    # fmt:on

    rows: list[Row] = []
    known_conditional_keys = {"when", "show"}
    for form_definition in form_definitions.iterator(chunk_size=10):
        component_keys: set[str] = set()
        for component in form_definition.configuration_wrapper:
            if not (conditional := component.get("conditional")):
                continue
            elif (
                "eq" in conditional
            ):  # no changes were made to the conditional property
                continue

            conditional_values = [
                conditional.get(key, empty) for key in known_conditional_keys
            ]

            if all((value == empty) for value in conditional_values) or all(
                value for value in conditional_values
            ):
                continue

            component_keys.add(component["key"])

        if not component_keys:
            continue

        form_mapping: dict[Form, set[FormStep]] = defaultdict(set[FormStep])
        for step in form_definition.formstep_set.all():
            form_mapping[step.form].add(step)

        for form, applicable_steps in form_mapping.items():
            row = Row(
                form_definition.pk,
                form_definition.name,
                component_keys,
                {str(step.uuid) for step in applicable_steps},
                form.admin_name,
                form.pk,
            )
            rows.append(row)

    rows.sort(key=lambda row: (row.form_definition_id, row.form_id))

    if not rows:
        click.echo(click.style("No applicable form definitions found.", fg="green"))
        return True

    click.echo(
        click.style(
            "Found possible form definition configurations with unwanted changes.",
            fg="red",
        )
    )
    click.echo("")
    click.echo(
        tabulate(
            rows,
            headers=(
                "Form definition ID",
                "Form definition name",
                "Component keys",
                "Form steps",
                "Form admin name",
                "Form ID",
            ),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_configurations()


if __name__ == "__main__":
    main()
