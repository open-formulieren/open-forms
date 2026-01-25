#!/usr/bin/env python
#
# Show which rules need a manual check after adding a step to the "disable next" action,
# to make sure it is the correct one. Note that the actual addition of a step happens in
# a migration. The output of the script is the same, independent of whether it was
# executed before or after the migration. Use the flag '--show-all' to list all rules
# which will be affected by the migration.
#
import sys
from collections.abc import Collection
from pathlib import Path

import django

import click
from tabulate import tabulate
from tqdm import tqdm

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def resolve_key(input_key: str, all_form_variable_keys: Collection[str]) -> str | None:
    """
    Resolve a (nested) key to its corresponding form variable key.

    Submission data of container-type components (e.g. editgrid, selectboxes, etc.)
    can be accessed with dot notation in a ``FormioData`` instance, but also in JSON
    logic. For example, key "selectboxes.a" with data ``{"a": "A", "b": "B"}``. This
    routine resolves the form variable key that corresponds to this data access key.

    :param input_key: The key to resolve.
    :param all_form_variable_keys: Collection of form variable keys to resolve for.
    :return: The resolved form variable key, or ``None`` if not resolved.
    """
    # There is a variable with this exact key, it is a valid reference.
    if input_key in all_form_variable_keys:
        return input_key

    # Process nested paths (editgrid, selectboxes, partners, children). Note that this
    # doesn't include other nested fields anymore, e.g. a textfield component with key
    # "foo.bar" will have already been resolved. We process all slices, as these keys
    # could also include dots.
    parts = input_key.split(".")
    for i in range(1, len(parts)):
        if (key := ".".join(parts[:i])) in all_form_variable_keys:
            return key

    # If none of the slices exist, we cannot resolve the complete key, so we just
    # return `None`. Note that the digest email should notify the user of invalid
    # logic rules.
    return None


def report_disable_next_logic_action_manual_check(show_all=False):
    from openforms.formio.service import iter_components
    from openforms.forms.models import Form, FormLogic, FormStep, FormVariable
    from openforms.utils.json_logic import introspect_json_logic

    queryset = Form.objects.prefetch_related(
        "formlogic_set", "formvariable_set", "formstep_set"
    )
    rules_that_need_check = []
    rules_with_disable_action = []
    for form in tqdm(
        queryset.iterator(),
        desc="Forms processed",
        total=queryset.count(),
        dynamic_ncols=True,
        mininterval=0.5,
        unit="form",
    ):
        # We don't care about deleted forms
        if form._is_deleted:
            continue

        # Set of logic rules which contain a "disable next" action.
        logic_rules: set[FormLogic] = {
            rule
            for rule in form.formlogic_set.all()
            for action in rule.actions
            if action["action"]["type"] == "disable-next"
        }
        # Exit early if none of the rules contain a disable next action
        if not logic_rules:
            continue

        # Mapping from component to step for quick access
        form_steps = form.formstep_set.select_related("form_definition")
        component_to_step: dict[str, FormStep] = {
            component["key"]: step
            for step in form_steps.iterator()
            for component in iter_components(
                step.form_definition.configuration,
                recursive=True,
                recurse_into_editgrid=False,
            )
        }
        form_variables: dict[str, FormVariable] = {
            var.key: var for var in form.formvariable_set.iterator()
        }

        # Process logic rules
        for rule in sorted(logic_rules, key=lambda rule: rule.order):
            rules_with_disable_action.append(
                [form.admin_name, rule.order + 1, rule.description]
            )
            if show_all:
                # Do not process anything if the user only wants to view all logic rules
                # with a "disable next" action.
                continue

            # Create a set of input variable steps by analyzing the logic trigger.
            input_variable_steps = set()
            for input_var in introspect_json_logic(
                rule.json_logic_trigger
            ).get_input_keys():
                form_variable_key = resolve_key(input_var.key, form_variables)
                if (form_variable := form_variables.get(form_variable_key)) is None:
                    continue

                if form_variable.prefill_plugin:
                    # If the variable has prefill configured -> add the first step.
                    # This is because prefilled data will be available upon submission
                    # creation, so the rule _could_ be triggered on the first step. If
                    # prefill did not succeed, we still need to execute it on step of
                    # the input variable as well, because the user might be asked to
                    # fill in the data manually.
                    input_variable_steps.add(form_steps.first())

                # Note that we also add `None` if we cannot resolve a step (form
                # variable is user defined). This is different from the migration -
                # where we don't add anything and assign the first step later - because
                # we want to notify the form designers to check these rules.
                step = component_to_step.get(form_variable.key, None)
                input_variable_steps.add(step)

            for action in rule.actions:
                if action["action"]["type"] != "disable-next":
                    continue

                if len(input_variable_steps) == 0:
                    # There are no input variables from the logic trigger, so we assign
                    # the first step as a best guess in the migration
                    # ("trigger_from_step" overrides it).
                    if rule.trigger_from_step:
                        continue

                    rules_that_need_check.append(
                        [
                            form.admin_name,
                            rule.order + 1,
                            rule.description,
                            "First step assigned as best guess",
                        ]
                    )

                elif None in input_variable_steps:
                    # If one of the variables is user defined -> mark this rule for a
                    # manual check. User-defined variables can be set with prefilled
                    # data, but also with user input through other logic rules, so we
                    # cannot be sure of the step. The only way to do this properly would
                    # be to have the full logic rule graph available.
                    rules_that_need_check.append(
                        [
                            form.admin_name,
                            rule.order + 1,
                            rule.description,
                            "JSON logic trigger contains user-defined variable",
                        ]
                    )

                elif len(input_variable_steps) == 1:
                    # If there is only one step, we assign it to the action in the
                    # migration ("trigger_from_step" overrides it). Not necessary to
                    # perform a manual check.
                    pass
                else:
                    # If we have multiple input steps, we add new actions for each step.
                    # If "trigger_from_step" is defined, any steps before this step are
                    # removed. Not necessary to perform a manual check.
                    pass

    if show_all:
        click.echo(
            click.style(
                "The following rules contain a 'disable next' action", fg="yellow"
            )
        )
        click.echo(
            tabulate(
                rules_with_disable_action,
                headers=("Form", "Rule number", "Rule description"),
            )
        )
        return

    if not rules_that_need_check:
        click.echo(click.style("No rules need a manual check", fg="green"))
        return

    click.echo(
        click.style(
            "Found 'disable next' actions which need a manual check.\n"
            "For the following rules, please make sure that the assigned step to the "
            "'disable next' action is the correct one.\n"
            "Note that it is possible to create more 'disable next' actions to assign "
            "additional steps if necessary.",
            fg="red",
        ),
    )
    click.echo(
        tabulate(
            rules_that_need_check,
            headers=("Form", "Rule number", "Rule description", "Reason"),
        )
    )


@click.command()
@click.option(
    "--show-all",
    is_flag=True,
    default=False,
    help=(
        "Show all logic rules that contain a 'disable next' action, and will therefore "
        "be affected by the data migration"
    ),
)
def cli(show_all: bool):
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    report_disable_next_logic_action_manual_check(show_all)


if __name__ == "__main__":
    cli()
