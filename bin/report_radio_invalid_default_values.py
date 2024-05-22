#!/usr/bin/env python
import django

from tabulate import tabulate


def report_null_values() -> bool:
    from openforms.forms.models import FormDefinition

    problems = []

    form_definitions = FormDefinition.objects.iterator()
    for fd in form_definitions:
        for component in fd.iter_components():
            default_value = component["defaultValue"]

            if (
                component["type"] == "radio"
                and isinstance(default_value, str)
                and bool(default_value)
            ):
                expected_values = [
                    radio_value["value"] for radio_value in component["values"]
                ]

                if default_value not in expected_values:
                    problems.append(
                        [
                            fd,
                            component["label"],
                            default_value,
                        ]
                    )

    if not problems:
        print("No invalid default values found.")
        return True

    print("Found invalid default values in form definition radio components.")
    print("")
    print(
        tabulate(
            problems,
            headers=("Form definition", "Component label", "Invalid value"),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_null_values()


if __name__ == "__main__":
    main()
