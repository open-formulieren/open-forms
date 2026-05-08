from traceback import format_exc

from django.core.management import BaseCommand
from django.db import transaction

from tabulate import tabulate

from ...logic_analysis import CyclesDetected
from ...models import Form


class Command(BaseCommand):
    help = """
    Enable new logic evaluation for all forms.

    Note that this will re-order the logic rules and remove any 'trigger from step'
    setting, which cannot be easily reverted. So, for large forms, it is recommended
    to create a copy of the form first, and enable the new logic evaluation feature flag
    manually before running this command.

    Any forms which contain rules with cycles will not be converted, and need to be
    resolved manually as well. If such forms exist, the output will contain a list of
    relevant form details.
    """

    def handle(self, **options):
        forms_to_convert = Form.objects.filter(
            _is_deleted=False, new_logic_evaluation_enabled=False
        )

        if not forms_to_convert.exists():
            self.stdout.write("All forms are already converted.")
            return

        forms_with_cycles_information = []
        forms_to_update = []
        n_updated_forms = 0
        for form in forms_to_convert.iterator():
            form.new_logic_evaluation_enabled = True

            if form.is_appointment or not form.form_step_map:
                n_updated_forms += 1
                forms_to_update.append(form)
                continue

            try:
                with transaction.atomic():
                    form.apply_logic_analysis()
                    form.formlogic_set.filter(trigger_from_step__isnull=False).update(
                        trigger_from_step=None
                    )
                    form.save(update_fields=["new_logic_evaluation_enabled"])
            except CyclesDetected as exc:
                variables = {var for cycle in exc.cycles for var in cycle.variables}
                form.new_logic_evaluation_enabled = False
                forms_with_cycles_information.append(
                    (
                        form.pk,
                        form.admin_name,
                        form.active,
                        ", ".join(sorted(variables)),
                    )
                )
            except Exception:
                form.new_logic_evaluation_enabled = False
                self.stdout.write(
                    f"Unexpected error while converting form '{form.admin_name} "
                    f"({form.pk})': \n{format_exc()}"
                )
            else:
                n_updated_forms += 1

        Form.objects.bulk_update(forms_to_update, ["new_logic_evaluation_enabled"])
        self.stdout.write(
            f"New logic evaluation has been enabled for {n_updated_forms} form(s)."
        )

        if forms_with_cycles_information:
            self.stdout.write(
                "\nThe following forms still contain cycles, and were therefore "
                "not updated. Please review them manually."
            )
            self.stdout.write(
                tabulate(
                    forms_with_cycles_information,
                    headers=(
                        "Form ID",
                        "Form name",
                        "Active",
                        "Variables in cycles",
                    ),
                )
            )
