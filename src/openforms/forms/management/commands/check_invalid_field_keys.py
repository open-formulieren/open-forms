from typing import List

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.urls import reverse

from tabulate import tabulate

from openforms.formio.utils import iter_components
from openforms.typing import JSONObject

from ...models import FormDefinition
from ...models.form_variable import variable_key_validator


class Command(BaseCommand):
    help = "Check if there are form definitions with invalid component keys."

    def handle(self, *args, **options):
        forms_definitions = FormDefinition.objects.only("pk", "name", "configuration")

        table_rows = []
        for form_definition in forms_definitions:
            invalid_keys = self.check_keys(form_definition.configuration)
            if invalid_keys:
                admin_path = reverse(
                    "admin:forms_formdefinition_change", args=(form_definition.pk,)
                )
                for index, key in enumerate(invalid_keys):
                    if index == 0:
                        row = [f"{form_definition.name} (URL: {admin_path})", key]
                    else:
                        row = ["", key]
                    table_rows.append(row)

        if not table_rows:
            self.stdout.write(
                self.style.SUCCESS("No form definitions with invalid keys.")
            )
            return

        self.stdout.write(
            self.style.ERROR(
                "\nThe following form definitions have invalid component keys:\n"
            )
        )

        table = tabulate(table_rows, headers=["Form definition", "Component key"])
        for line in table.splitlines():
            self.stdout.write(line)

        raise CommandError()

    def check_keys(self, configuration: JSONObject) -> List[str]:
        invalid_keys = []
        for component in iter_components(configuration):
            try:
                variable_key_validator(component["key"])
            except ValidationError:
                invalid_keys.append(component["key"])

        return invalid_keys
