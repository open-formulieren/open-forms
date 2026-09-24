from django.core.management import BaseCommand, CommandError
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

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-dry-run",
            "--no-dryrun",
            action="store_false",
            dest="dry_run",
            help="Also execute the reported changes",
        )

    def handle(self, **options):
        dry_run = options["dry_run"]
        forms_to_convert = Form.objects.filter(
            _is_deleted=False, new_logic_evaluation_enabled=False
        )

        if not forms_to_convert.exists():
            self.stdout.write("All forms are already converted.")
            return

        forms_with_cycles_information: list[tuple[int, str, bool, str]] = []
        forms_with_errors_during_conversion: list[tuple[int, str, bool]] = []
        forms_to_skip_analysis: list[Form] = []
        updated_forms: list[tuple[int, str, bool]] = []
        for form in forms_to_convert.iterator():
            form.new_logic_evaluation_enabled = True

            if form.is_appointment or not form.form_step_map:
                forms_to_skip_analysis.append(form)
                continue

            try:
                # Applying logic evaluation can take some time, so to avoid having to
                # do successful conversions again, use a transaction for each individual
                # form
                with transaction.atomic():
                    form.apply_logic_analysis()
                    form.formlogic_set.filter(trigger_from_step__isnull=False).update(
                        trigger_from_step=None
                    )
                    form.save(update_fields=["new_logic_evaluation_enabled"])

                    if dry_run:
                        transaction.set_rollback(True)
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
                forms_with_errors_during_conversion.append(
                    (form.pk, form.admin_name, form.active)
                )
            else:
                updated_forms.append((form.pk, form.admin_name, form.active))

        with transaction.atomic():
            Form.objects.bulk_update(
                forms_to_skip_analysis, ["new_logic_evaluation_enabled"]
            )
            updated_forms.extend(
                [
                    (form.pk, form.admin_name, form.active)
                    for form in forms_to_skip_analysis
                ]
            )
            if dry_run:
                transaction.set_rollback(True)

        if updated_forms:
            self.stdout.write(
                "New logic evaluation has been enabled for the following forms:"
            )
            self.stdout.write(
                tabulate(
                    updated_forms,
                    headers=(
                        "Form ID",
                        "Form name",
                        "Active",
                    ),
                )
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

        if forms_with_errors_during_conversion:
            self.stderr.write(
                "\nConversion of the following forms failed unexpectedly. Please "
                "review them manually and/or contact support."
            )
            self.stderr.write(
                tabulate(
                    forms_with_errors_during_conversion,
                    headers=(
                        "Form ID",
                        "Form name",
                        "Active",
                    ),
                )
            )

        if forms_with_errors_during_conversion or forms_with_cycles_information:
            raise CommandError(
                "Not all forms could be converted, please review the output."
            )
