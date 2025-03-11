#!/usr/bin/env python
#
# Fix the `variables_mapping` value in the options configuration of Objects API
# registration backends.
#
# Due to a missing default value, some Objects API registrations don't have
# `variables_mapping` in their `options` configuration. As this value is used when
# configuring variable mappings, the missing `variables_mapping` causes javascript
# errors.
#
# This script automatically fixes all options `variables_mapping` values for Objects API
# registrations. Any missing or incorrect `variables_mapping` is set to `[]`.
# Related to ticket: https://github.com/open-formulieren/open-forms/issues/5031
from __future__ import annotations

import sys
from pathlib import Path

import django
from django.db.models import Q

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def fix_objects_api_registration_variables_mapping():
    from openforms.forms.models import FormRegistrationBackend
    from openforms.registrations.contrib.objects_api.config import VersionChoices

    form_registrations_to_update = []
    registration_backends = (
        FormRegistrationBackend.objects.filter(backend="objects_api")
        .filter(~Q(options__version=VersionChoices.V1))
        .iterator()
    )

    # Only Objects API registration of version 2, or without a version, will be present
    for objects_api_registration in registration_backends:
        should_update = False

        # The objects_api_registration should always have a version, but just to be sure
        if not objects_api_registration.options.get("version", None):
            objects_api_registration.options["version"] = VersionChoices.V2
            should_update = True

        variables_mapping = objects_api_registration.options.get(
            "variables_mapping", None
        )
        if not isinstance(variables_mapping, list):
            objects_api_registration.options["variables_mapping"] = []
            should_update = True

        if should_update:
            form_registrations_to_update.append(objects_api_registration)

    FormRegistrationBackend.objects.bulk_update(
        form_registrations_to_update, fields=["options"]
    )


def main(**kwargs):
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    return fix_objects_api_registration_variables_mapping(**kwargs)


if __name__ == "__main__":
    main()
