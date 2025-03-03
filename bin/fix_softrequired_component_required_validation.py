#!/usr/bin/env python
#
# Fix the validation set on soft-required components.
#
# Due to a bug in the global configuration, the validation for soft-required components
# could be set to `required: true`. This causes the form to be in-completable, as the
# user cannot provide a value for the soft-required component.
# The problem in the global configuration has been fixed, so new soft-required component
# won't have this issue.
#
# This script automatically fixes the validation rules of all soft-required components.
# Related to ticket: https://github.com/open-formulieren/open-forms/issues/5090
from __future__ import annotations

import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def fix_softrequired_required_validation() -> None:
    from django.db.models import Q

    from openforms.forms.models import FormDefinition

    form_definitions_to_update = []
    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        # Flag to update Form Definition. Is set when child component is changed
        should_persist_fd = False

        for component in form_definition.iter_components():
            # The fix is only needed for softRequiredErrors components
            if component["type"] != "softRequiredErrors":
                continue

            # Only fix components with the required validation set to True
            if not component["validate"].get("required", False):
                continue

            component["validate"]["required"] = False
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

    return fix_softrequired_required_validation(**kwargs)


if __name__ == "__main__":
    main()
