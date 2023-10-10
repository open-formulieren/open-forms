#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_non_unique_steps() -> bool:
    from django.db.models import Count

    from openforms.forms.models import Form, FormDefinition, FormStep

    # query for form definitions used multiple times in a form
    qs = (
        FormStep.objects.values("form", "form_definition")
        .annotate(occurrences=Count("form_definition"))
        .filter(occurrences__gt=1)
        .order_by()  # reset ordering (implicitly added by django-ordered-model)
    )
    num = qs.count()
    if not num:
        print("No forms found with duplicated form steps.")
        return True

    # report which forms have issues
    forms = Form.objects.filter(pk__in=qs.values_list("form")).in_bulk()
    form_definitions = FormDefinition.objects.filter(
        pk__in=qs.values_list("form_definition")
    ).in_bulk()

    duplicates = []
    for item in qs:
        form = forms[item["form"]]
        form_definition = form_definitions[item["form_definition"]]

        duplicates.append(
            [
                form.admin_name,
                form_definition.admin_name,
                item["occurrences"],
            ]
        )

    print("Found forms with duplicated steps.")
    print("")
    print(
        tabulate(
            duplicates,
            headers=("Form", "Form step", "Occurrences"),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_non_unique_steps()


if __name__ == "__main__":
    main()
