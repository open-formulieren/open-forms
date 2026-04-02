#!/usr/bin/env python
from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import django
from django.db import transaction

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

type Row = tuple[int, str]


def report_invalid_forms() -> bool:
    """
    Query forms that have new logic evaluation enabled but inconsistent logic rule
    configuration.
    """
    from openforms.forms.logic_analysis import CyclesDetected
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

    # check each individual form for logic rule cycles. Run this in a transaction and
    # roll back, because apply_logic_analysis() saves the result to the DB.
    forms_to_check = Form.objects.filter(
        _is_deleted=False,
        new_logic_evaluation_enabled=False,
        formlogic__isnull=False,
    ).distinct()

    transaction.set_autocommit(False)
    cycles_detected = False

    def _detect_cycles() -> Iterator[tuple[int, str, bool, str]]:
        nonlocal cycles_detected

        for form in forms_to_check.iterator():
            form.new_logic_evaluation_enabled = True
            try:
                form.apply_logic_analysis()
            except CyclesDetected as exc:
                variables = {var for cycle in exc.cycles for var in cycle.variables}
                cycles_detected = True
                yield (form.pk, form.admin_name, form.active, ", ".join(variables))

    try:
        print(
            tabulate(
                _detect_cycles(),
                headers=("Form ID", "Form name", "Active", "Variables in cycles"),
            )
        )
    finally:
        transaction.rollback()

    if cycles_detected:
        print(
            "\nThe table above lists all the forms where cycles in logic rules were "
            "detected. Please review and fix them as soon as possible. Open Forms 4.0 "
            "will require this to be resolved before you can upgrade."
        )

    return not invalid_rules_detected and not cycles_detected


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_invalid_forms()


if __name__ == "__main__":
    main()
