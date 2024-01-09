#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def report_problems() -> bool:
    from openforms.forms.models import FormDefinition

    problems = []

    fds = FormDefinition.objects.iterator()
    for form_definition in fds:
        for component in form_definition.iter_components():
            assert "key" in component
            assert "type" in component

            problem_base = [
                form_definition.admin_name,
                component.get("label") or component["key"],
                component["type"],
            ]

            match component:
                case {"type": "file", "defaultValue": list() as default_value}:
                    if None in default_value:
                        problems.append([*problem_base, "'null' in file default value"])

                case {"type": "columns", "columns": list() as columns}:
                    for col in columns:
                        has_problem = False
                        if (
                            not (size := col.get("size"))
                            or not isinstance(size, int)
                            or not 1 <= size <= 12
                        ):
                            has_problem = True

                        if not (size_mobile := col.get("sizeMobile")):
                            if not has_problem:
                                continue

                        if (
                            not isinstance(size_mobile, int)
                            or not 1 <= size_mobile <= 4
                        ):
                            has_problem = True

                        if has_problem:
                            problems.append(
                                [
                                    *problem_base,
                                    "column (mobile) size is not an integer",
                                ]
                            )
                            break

    if not problems:
        print("No problems found.")
        return True

    print("Found problems in form definition components.")
    print("")
    print(
        tabulate(
            problems,
            headers=("Form definition", "Component label", "Component type", "Problem"),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_problems()


if __name__ == "__main__":
    main()
