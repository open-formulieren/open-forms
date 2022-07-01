# reported via Taiga Den Haag, issue #103
#
# Execute by running:
#
#   python bin/fix_default_values_formio.py
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
    from openforms.config.models import GlobalConfiguration

    config = GlobalConfiguration.get_solo()

    for form_definition in FormDefinition.objects.all().iterator():
        fix_form_definition(form_definition, config.enable_form_variables)


def get_empty_value(component):
    from openforms.forms.constants import FormVariableDataTypes
    from openforms.forms.models.form_variable import INITIAL_VALUES, COMPONENT_DATATYPES


    component_type = component["type"]
    data_type = COMPONENT_DATATYPES.get(component_type) or FormVariableDataTypes.string
    return INITIAL_VALUES[data_type]


def fix_form_definition(fd, update_form_variables):
    from openforms.forms.models.form_variable import FormVariable
    changed = False

    variables_to_change = []

    for component in fd.iter_components(recursive=True):
        if not component.get("multiple") and isinstance(component.get("defaultValue"), list):
            empty_value = get_empty_value(component)
            component["defaultValue"] = empty_value
            changed = True

            if update_form_variables:
                variable = FormVariable.objects.get(key=component["key"], form_definition=fd)
                variable.initial_value = empty_value
                variables_to_change.append(variable)

    if changed:
        fd.save(update_fields=["configuration"])
        print(f"Updated form definition {fd.id} ({fd.admin_name})")

        if update_form_variables:
            FormVariable.objects.bulk_update(variables_to_change, fields=["initial_value"])


if __name__ == "__main__":
    main()
