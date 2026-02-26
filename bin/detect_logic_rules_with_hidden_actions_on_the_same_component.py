import sys
from pathlib import Path

import django

import click

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def detect_logic_rules_with_hidden_actions_on_the_same_component():
    from openforms.formio.utils import iter_components
    from openforms.forms.models import Form

    queryset = Form.objects.prefetch_related("formlogic_set", "formstep_set")

    affected_forms = set()
    for form in queryset:
        if form._is_deleted:
            continue

        rules = form.formlogic_set.all()
        if not rules:
            continue

        # Mapping from component key to configuration for quick access
        form_steps = form.formstep_set.select_related("form_definition")
        component_to_configuration = {
            component["key"]: component
            for step in form_steps
            for component in iter_components(
                step.form_definition.configuration,
                recursive=True,
                recurse_into_editgrid=False,
            )
        }

        is_form_affected = False
        components_with_hidden_action = set()
        for rule in rules:
            for action in rule.actions:
                # We only care about 'hidden' property actions
                if (
                    action["action"]["type"] != "property"
                    or action["action"]["property"]["value"] != "hidden"
                ):
                    continue

                # `.get` to account for (possible) broken rules
                key = action["component"]
                if (configuration := component_to_configuration.get(key)) is None:
                    continue

                # Might be dealing with layout components. Note that it is probably a
                # rare edge case, because it implies one rule has an action on the whole
                # layout component, and another one only on a child of it.
                affected_components = {
                    child["key"]
                    for child in iter_components(
                        configuration, recursive=True, recurse_into_editgrid=False
                    )
                }
                affected_components.add(key)

                if not components_with_hidden_action.isdisjoint(affected_components):
                    is_form_affected = True
                    break
                components_with_hidden_action.update(affected_components)

            if is_form_affected:
                break

        if is_form_affected:
            affected_forms.add(form.admin_name)

    if not affected_forms:
        click.echo(click.style("No forms are affected", fg="green"))

    click.echo(click.style("Affected forms:\n", fg="red"))
    for form_name in affected_forms:
        click.echo(click.style(form_name, fg="red"))


@click.command()
def cli():
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    detect_logic_rules_with_hidden_actions_on_the_same_component()


if __name__ == "__main__":
    cli()
