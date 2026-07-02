# GH-5977 removed the ability to apply the "disable/read-only" logic to Fieldsets.
# This is causing problems in existing forms that have been configured in such a way.
# This script finds these problematic forms and all components within the fieldset get
# added to the logic rule as "disable" actions.

import sys
from pathlib import Path

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def mark_children_as_disabled(component_configuration):
    children_actions = []
    if component_configuration["type"] == "fieldset":
        for child_component in component_configuration.get("components", []):
            children_actions.extend(mark_children_as_disabled(child_component))
    else:
        children_actions.append(
            {
                "action": {
                    "type": "property",
                    "state": True,
                    "property": {
                        "type": "bool",
                        "value": "disabled",
                    },
                },
                "component": component_configuration["key"],
            }
        )

    return children_actions


def update_fieldset_logic_rules(dry_run: bool = False) -> bool:

    from openforms.formio.service import iter_components
    from openforms.formio.typing.vanilla import FieldsetComponent
    from openforms.forms.models import Form, FormLogic

    forms_to_check = Form.objects.filter(_is_deleted=False).prefetch_related(
        "formlogic_set", "formstep_set"
    )

    # track the fieldset keys that we had to update (fieldsets with disabled -> make their
    # children disabled)
    updated_fieldsets = []
    for form in forms_to_check.iterator(chunk_size=10):
        form_logics = FormLogic.objects.filter(form=form)
        if not form_logics:
            continue

        # mappings of fieldset components (component_key: component_configuration)
        component_map: dict[str, FieldsetComponent] = {}

        form_steps = form.formstep_set.select_related("form_definition")
        for form_step in form_steps:
            for component in iter_components(
                form_step.form_definition.configuration,
                recursive=True,
                recurse_into_editgrid=False,
            ):
                if component["type"] == "fieldset":
                    component_map[component["key"]] = component

        for rule in form.formlogic_set.iterator():
            # the final logic actions we will have in the form
            updated_logic_actions = []
            for action in rule.actions:
                # make sure we only get the fieldsets that have disabled property wrongly
                # set
                if (
                    action["component"] in component_map
                    and action["action"]["property"]["value"] == "disabled"
                ):
                    updated_logic_actions.extend(
                        mark_children_as_disabled(component_map[action["component"]])
                    )
                    updated_fieldsets.append(
                        (
                            form.admin_name,
                            action["component"],
                        )
                    )
                else:
                    updated_logic_actions.append(action)

            if dry_run:
                continue

            rule.actions = updated_logic_actions
            rule.save()

    if not updated_fieldsets:
        click.echo(
            click.style(
                "There are not fieldset components with disabled property.", fg="green"
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
            [(fieldset[0], fieldset[1]) for fieldset in updated_fieldsets],
            headers=(
                "Form",
                "Updated keys (fieldsets)",
            ),
        )
    )

    return False


def main(skip_setup: bool = False, dry_run: bool = False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return update_fieldset_logic_rules(dry_run=dry_run)


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
