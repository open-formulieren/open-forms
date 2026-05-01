#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

type Row = tuple[str, int, str, str]


def report_address_derivation_usage():
    """
    Inspect all form definitions used in at least one form for address derivation usage.

    Address derivation in textfields in the new renderer is not supported. Users must
    convert their forms to use addressNL which now handles this feature.
    """
    from openforms.forms.models import Form, FormDefinition

    # Ignore form definitions that aren't used in any form
    form_definitions = (
        FormDefinition.objects.exclude(formstep__isnull=True).distinct().order_by("pk")
    )

    problems: list[Row] = []

    for form_definition in form_definitions.iterator():
        components: list[str] = []

        for component in form_definition.configuration_wrapper:
            if component["type"] != "textfield":
                continue

            match component:
                case {
                    "deriveCity": bool() as derive,
                    "deriveHouseNumber": str() as house_number_ref,
                    "derivePostcode": str() as postcode_ref,
                } | {
                    "deriveStreetName": bool() as derive,
                    "deriveHouseNumber": str() as house_number_ref,
                    "derivePostcode": str() as postcode_ref,
                } if derive and house_number_ref and postcode_ref:
                    identification = f"{component['label']} ({component['key']})"
                    registration = (
                        f" -> {reg_attr}"
                        if (
                            reg_attr := component.get("registration", {}).get(
                                "attribute"
                            )
                        )
                        else ""
                    )
                    components.append(f"{identification}{registration}")
                case _:
                    continue

        if not components:
            continue

        used_in_forms = form_definition.used_in

        def _get_form_registration_backends(form: Form) -> str:
            backends = ",".join(
                backend
                for backend in form.registration_backends.values_list(
                    "backend", flat=True
                ).distinct()
            )
            if not backends:
                return ""
            return f", registration: {backends}"

        problems.append(
            (
                form_definition.admin_name,
                form_definition.pk,
                "\n".join(components),
                "\n".join(
                    f"{form.admin_name} (ID: {form.pk}{_get_form_registration_backends(form)})"
                    for form in used_in_forms
                ),
            )
        )

    if not problems:
        print("No usages found.")
        return True

    print(
        tabulate(
            problems,
            headers=(
                "Form definition",
                "ID",
                "Components",
                "Used in forms",
            ),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_address_derivation_usage()


if __name__ == "__main__":
    main()
