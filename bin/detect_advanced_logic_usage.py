#!/usr/bin/env python
# Execute by running:
#
#   python bin/detect_advanced_logic_usage.py
#
import sys
from operator import attrgetter
from pathlib import Path
from typing import List

import django

from glom import glom
from glom.reduction import itertools

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def main():
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    report_advanced_logic_usage()


def has_client_side_logic_usage(component: dict):
    advanced_logic = glom(component, "logic", default=[])
    return len(advanced_logic) > 0


def report_advanced_logic_usage():
    from django.urls import reverse

    from openforms.forms.models import FormStep

    affected_forms: List[FormStep] = []

    form_steps = FormStep.objects.select_related("form_definition", "form")
    for form_step in form_steps:
        for component in form_step.iter_components():
            if has_client_side_logic_usage(component):
                affected_forms.append(form_step)
                break

    if not affected_forms:
        print("Geen formulieren die logica in de 'geavanceerd' tab gebruiken.")
        return

    def key_func(form_step):
        return form_step.form.pk

    affected_forms = sorted(affected_forms, key=key_func)
    for form, steps in itertools.groupby(affected_forms, key=attrgetter("form")):
        admin_path = reverse("admin:forms_form_change", args=(form.pk,))
        print(f"Formulier: {form.admin_name} (URL: {admin_path})")
        for step in steps:
            print(f"  Stap: {step.form_definition.admin_name}")


if __name__ == "__main__":
    main()
