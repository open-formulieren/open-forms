from typing import List

from django.core.management import BaseCommand, CommandError

from tabulate import tabulate

from openforms.formio.utils import iter_components

from ...models import Form


class Command(BaseCommand):
    help = "Check if there are forms with components with duplicate keys."

    def handle(self, *args, **options):
        forms = Form.objects.only("id", "name")

        duplicates = []
        for form in forms:
            duplicate_keys = self.get_duplicate_keys(form)
            if duplicate_keys:
                duplicates += duplicate_keys

        if not duplicates:
            self.stdout.write(
                self.style.SUCCESS(
                    "No forms with duplicate keys in the form definitions found."
                )
            )
            return

        self.stdout.write(self.style.ERROR("\nFound the following duplicates:\n"))

        table = tabulate(duplicates, headers=["Form", "Form Step", "Component key"])
        for line in table.splitlines():
            self.stdout.write(line)

        raise CommandError("Please fix the duplicate keys")

    def get_duplicate_keys(self, form: Form) -> List[List[str]]:
        form_steps = form.formstep_set.select_related("form_definition").only(
            "form_definition__configuration", "form_definition__name"
        )

        duplicates = []

        existing_keys = []
        for form_step in form_steps:
            form_definition_configuration = form_step.form_definition.configuration
            for component in iter_components(
                configuration=form_definition_configuration, recursive=True
            ):
                if component["key"] in existing_keys:
                    duplicates.append(
                        [form.name, form_step.form_definition.name, component["key"]]
                    )
                else:
                    existing_keys.append(component["key"])

        return duplicates
