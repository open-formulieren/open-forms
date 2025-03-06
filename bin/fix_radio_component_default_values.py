#!/usr/bin/env python
#
# Fix the `defaultValue` of radio components.
#
# Due to a bug in the form editor, when a radio component had a defaultValue of ""
# (empty string) it would automatically be set to `null`. This in turn could cause json
# logic to stop working properly, due to the defaultValue being changed.
#
# This script automatically fixes all defaultValues of radio components that where set
# to `null`.
# Related to ticket: https://github.com/open-formulieren/open-forms/issues/5104
from __future__ import annotations

import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def fix_radio_component_default_values():
    from openforms.forms.models import FormDefinition

    form_definitions_to_update = []
    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        # Flag to update Form Definition. Is set when child component is changed
        should_persist_fd = False

        for component in form_definition.iter_components():
            # The fix is only needed for radio components whose defaultValue is `None`
            if component["type"] != "radio" or component["defaultValue"] is not None:
                continue

            component["defaultValue"] = ""
            # Set flag to update Form Definition
            should_persist_fd = True

        if should_persist_fd:
            form_definitions_to_update.append(form_definition)

    FormDefinition.objects.bulk_update(
        form_definitions_to_update, fields=["configuration"]
    )


def main(**kwargs):
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    return fix_radio_component_default_values(**kwargs)


if __name__ == "__main__":
    main()
