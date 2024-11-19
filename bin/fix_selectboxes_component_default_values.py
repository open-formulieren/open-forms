#!/usr/bin/env python
#
# Fix the initial values of form variables related to selectboxes components.
#
# Due to a bug in the JSON parser, some of the form variable initial value don't match with
# their respective component default values. This bug is mostly an issue for selectboxes components.
# The problem in the JSON parser has been fixed, so new and updated forms won't have this issue.
#
# This script automatically fixes all initial values of the selectboxes component form variables.
# Related to ticket: https://github.com/open-formulieren/open-forms/issues/4810
from __future__ import annotations

import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def fix_selectboxes_default_values():
    from django.db.models import Q

    from openforms.formio.utils import get_component_default_value
    from openforms.forms.models import FormDefinition, FormVariable

    variables_to_update = []
    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        for component in form_definition.iter_components():
            # The fix is only needed for selectboxes components
            if component["type"] != "selectboxes":
                continue

            # Update all form variables related to the component and form definition,
            # when the form variable initial value doesn't match the component default value
            form_variables = FormVariable.objects.filter(
                ~Q(initial_value=get_component_default_value(component)),
                key=component["key"],
                form_definition_id=form_definition.id,
            )
            for form_variable in form_variables:
                form_variable.initial_value = get_component_default_value(component)
                variables_to_update.append(form_variable)

    FormVariable.objects.bulk_update(variables_to_update, fields=["initial_value"])


def main(**kwargs):
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    return fix_selectboxes_default_values(**kwargs)


if __name__ == "__main__":
    main()
