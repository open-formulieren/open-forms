# reported via Taiga Venray, issue #17
#
# Execute by running:
#
#   python bin/fix_selectboxes_multiple.py
#
import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def main():
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    from openforms.forms.models import FormDefinition

    for form_definition in FormDefinition.objects.all().iterator():
        fix_form_definition(form_definition)


def fix_form_definition(fd):
    changed = False

    for component in fd.iter_components(recursive=True):
        if component.get("type") != "selectboxes":
            continue

        if not component.get("multiple", False):
            continue

        component["multiple"] = False
        changed = True

    if changed:
        fd.save(update_fields=["configuration"])
        print(f"Updated form definition {fd.id} ({fd.admin_name})")


if __name__ == "__main__":
    main()
