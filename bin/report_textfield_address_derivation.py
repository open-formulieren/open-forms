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
    from openforms.forms.constants import LogicActionTypes
    from openforms.forms.models import Form, FormDefinition
    from openforms.utils.json_logic import introspect_json_logic

    # Ignore form definitions that aren't used in any form
    form_definitions = (
        FormDefinition.objects.exclude(formstep__isnull=True).distinct().order_by("pk")
    )

    problems: list[Row] = []

    for form_definition in form_definitions.iterator():
        components: list[str] = []
        component_keys: set[str] = set()

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
                    component_keys.add(component["key"])
                    component_keys.add(house_number_ref)
                    component_keys.add(postcode_ref)
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

        def _get_logic_usage(form: Form) -> str:
            for rule in form.formlogic_set.all():
                trigger = introspect_json_logic(rule.json_logic_trigger)
                has_usage = component_keys.intersection(  # noqa: B023
                    {input_var.key for input_var in trigger.get_input_keys()}
                )
                if has_usage:
                    return ", used in logic trigger"

                for action in rule.actions:
                    match action:
                        case {
                            "action": {"type": LogicActionTypes.property},
                            "component": str(key),
                        } if key in component_keys:  # noqa: B023
                            return ", used in logic action (property)"
                        case {
                            "action": {"type": LogicActionTypes.variable},
                            "variable": str(key),
                        }:
                            if key in component_keys:  # noqa: B023
                                return ", used in logic action (variable)"

                            value = introspect_json_logic(action["action"]["value"])
                            _has_usage = component_keys.intersection(  # noqa: B023
                                {input_var.key for input_var in value.get_input_keys()}
                            )
                            if _has_usage:
                                return (
                                    ", used in logic action (variable value expression)"
                                )
                        case {"action": {"type": LogicActionTypes.evaluate_dmn}}:
                            dmn_config = action["action"]["config"]
                            mappings = (
                                dmn_config["input_mapping"]
                                + dmn_config["output_mapping"]
                            )

                            if component_keys.intersection(  # noqa: B023
                                {mapping["form_variable"] for mapping in mappings}
                            ):
                                return ", used in logic action (evaluate_dmn)"

                        case {
                            "action": {
                                "type": LogicActionTypes.disable_next
                                | LogicActionTypes.step_not_applicable
                                | LogicActionTypes.step_applicable
                                | LogicActionTypes.synchronize_variables
                                | LogicActionTypes.fetch_from_service
                                | LogicActionTypes.set_registration_backend
                            }
                        }:
                            pass
            return ""

        problems.append(
            (
                form_definition.admin_name,
                form_definition.pk,
                "\n".join(components),
                "\n".join(
                    f"{form.admin_name} (ID: {form.pk}{_get_form_registration_backends(form)}{_get_logic_usage(form)})"
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
