#!/usr/bin/env python
#
# GH-5977 removed the ability to apply the "disable/read-only" logic to layout components.
# This is causing problems in existing forms that have been configured in such a way.
# This script finds these problematic forms and all components within the parent layout
# get added to the logic rule as "disable" actions.

import sys
from pathlib import Path

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def mark_children_as_disabled(component_configuration, action):
    from openforms.formio.service import holds_submission_data

    children_actions = []
    if holds_submission_data(component_configuration):
        children_actions.append(
            {
                "action": {
                    "type": "property",
                    "state": action["action"]["state"],
                    "property": {
                        "type": "bool",
                        "value": "disabled",
                    },
                },
                "component": component_configuration["key"],
            }
        )
    else:
        component_type = component_configuration["type"]

        if component_type == "fieldset":
            children = component_configuration.get("components", [])

        elif component_type == "columns":
            children = [
                child
                for column in component_configuration["columns"]
                for child in column.get("components")
            ]

        for child in children:
            children_actions.extend(mark_children_as_disabled(child, action))

    return children_actions


def update_layout_components_logic_rules(dry_run: bool = False) -> bool:

    from django.db import transaction

    from openforms.formio.service import holds_submission_data
    from openforms.formio.typing import Component
    from openforms.forms.models import Form

    forms_to_check = (
        Form.objects.filter(_is_deleted=False, formlogic__isnull=False)
        .distinct()
        .prefetch_related(
            "formlogic_set",
            "formstep_set",
        )
    )

    # track the layout components' keys that we had to update (layout componenents with
    # disabled -> make their children disabled)
    updated_layout_components = []
    for form in forms_to_check.iterator(chunk_size=10):
        # mappings of layout components (component_key: component_configuration)
        component_map: dict[str, Component] = {}

        for component in form.iter_components():
            if not holds_submission_data(component):
                component_map[component["key"]] = component

        if not component_map:
            continue

        with transaction.atomic():
            for rule in form.formlogic_set.iterator():
                # the final logic actions we will have in the form
                updated_logic_actions = []
                should_update = False
                for action in rule.actions:
                    if (
                        action.get("component") in component_map
                        and action["action"].get("property", {}).get("value")
                        == "disabled"
                    ):
                        updated_logic_actions.extend(
                            mark_children_as_disabled(
                                component_map[action["component"]], action
                            )
                        )
                        updated_layout_components.append(
                            (
                                form.admin_name,
                                action["component"],
                            )
                        )
                        should_update = True
                    else:
                        updated_logic_actions.append(action)

                if dry_run:
                    continue

                if should_update:
                    rule.actions = updated_logic_actions
                    rule.save(update_fields=["actions"])

    if not updated_layout_components:
        click.echo(
            click.style(
                "There are not layout components with disabled property.", fg="green"
            )
        )
        return True

    message = (
        "Logic rules that will be updated: " if dry_run else "Logic rules were updated."
    )
    click.echo(click.style(message, fg="yellow"))
    click.echo("")
    click.echo(
        tabulate(
            [(comp[0], comp[1]) for comp in updated_layout_components],
            headers=(
                "Form",
                "Updated keys (layout components)",
            ),
        )
    )

    return False


def main(skip_setup: bool = False, dry_run: bool = False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return update_layout_components_logic_rules(dry_run=dry_run)


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Do not perform any changes to the related logic rules.",
)
def cli(dry_run: bool):
    return main(dry_run=dry_run)


if __name__ == "__main__":
    cli()
