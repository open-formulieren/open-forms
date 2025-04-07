#!/usr/bin/env python
#
# Fix the default value of components.
#
# Because of incorrect default values of some components in the form builder, they were
# saved to the database with default value ``None``. On versions before 3.x, hidden
# components with the 'clearOnHide' property set, cause validation to be executed
# prematurely when filling out a form. This is due to a mismatch between the default
# value set by the backend while performing the clear-on-hide action (see
# evaluate_form_logic)
#
# This script automatically fixes the default value of all relevant components that
# were set to ``None``.
# Related tickets:
# - https://github.com/open-formulieren/open-forms/issues/4810
# - https://github.com/open-formulieren/open-forms/issues/5104
# - https://github.com/open-formulieren/open-forms/issues/5181
from __future__ import annotations

import sys
from pathlib import Path

import django

from openforms.setup import setup_env

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

COMPONENTS_TO_CHANGE = [
    "textfield",
    "radio",
    "file",
    "checkbox",
    "editgrid",
    "signature",
    "email",
    "time",
    "phoneNumber",
    "textarea",
    "iban",
    "licenseplate",
]


def fix_component_default_values():
    from openforms.formio.utils import get_component_empty_value
    from openforms.forms.models import FormDefinition

    form_definitions_to_update = []
    for form_definition in FormDefinition.objects.iterator():
        # Flag to update the form definition. Is set when any component of a form
        # definition is changed
        should_persist_fd = False

        for component in form_definition.iter_components():
            default_value = component.get("defaultValue")
            empty_value = get_component_empty_value(component)
            if (
                component["type"] not in COMPONENTS_TO_CHANGE
                or default_value is not None
                or default_value == empty_value
            ):
                continue

            component["defaultValue"] = empty_value
            should_persist_fd = True

        if should_persist_fd:
            form_definitions_to_update.append(form_definition)

    FormDefinition.objects.bulk_update(
        form_definitions_to_update, fields=["configuration"]
    )


def main():
    setup_env()
    django.setup()

    fix_component_default_values()


if __name__ == "__main__":
    main()
