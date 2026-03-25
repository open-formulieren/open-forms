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
    """
    from openforms.forms.models import Form

    forms = Form.objects.filter(
        new_logic_evaluation_enabled=True,
        formlogic__trigger_from_step__isnull=False,
    ).distinct()
    if not forms.exists():
        return True

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
    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_invalid_forms()


if __name__ == "__main__":
    main()
