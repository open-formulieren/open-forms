#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

type Row = tuple[int, str]


def report_invalid_forms() -> bool:
    """
    Query forms that have new logic evaluation enabled but inconsistent logic rule
    configuration.

    In 4.0, this script will be used as an upgrade check, which means we can also
    report forms that are not yet converted to new logic evalution at all.
    """
    from openforms.forms.models import Form

    invalid_rules_detected = False

    # check invalid existing forms that are perhaps migrated on the shell
    forms = Form.objects.filter(
        new_logic_evaluation_enabled=True,
        formlogic__trigger_from_step__isnull=False,
    ).distinct()
    if forms.exists():
        invalid_rules_detected = True
        print(
            "The following forms have at least one logic rule with 'trigger_from_step' "
            "set up, which is incompatible with the new logic evaluation."
        )
        print(
            tabulate(
                ((form.pk, form.admin_name) for form in forms.iterator()),
                headers=("Form ID", "Form name"),
            )
        )

    # check if any forms still have new logic evaluation disabled
    forms_to_check = Form.objects.filter(
        _is_deleted=False,
        new_logic_evaluation_enabled=False,
        formlogic__isnull=False,
    ).distinct()

    non_converted_forms_detected = False
    if forms_to_check.exists():
        non_converted_forms_detected = True
        print(
            "The following forms have have not been converted to the new logic "
            "evaluation. Please review and change them to upgrade to Open Forms 4.0."
        )
        print(
            tabulate(
                ((form.pk, form.admin_name) for form in forms_to_check.iterator()),
                headers=("Form ID", "Form name"),
            )
        )

    return not invalid_rules_detected and not non_converted_forms_detected


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_invalid_forms()


if __name__ == "__main__":
    main()
