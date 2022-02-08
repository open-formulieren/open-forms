import json
import os

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import transaction

from openforms.forms.tests import factories as form_factories


class Command(BaseCommand):
    help = "Load fixtures by using the factories"

    @transaction.atomic
    def handle(self, **options):
        # Load all fixtures present in `cypress/data_fixtures/`
        path = os.path.join(settings.BASE_DIR, "cypress/data_fixtures/definitions")
        for fixture in os.listdir(path):
            with open(f"{path}/{fixture}", "r") as f:
                data = json.load(f)
                for entry in data:
                    factory = getattr(form_factories, entry["factory"])
                    factory.create(**entry["params"])

        # Dump the generated data
        result_path = os.path.join(
            settings.BASE_DIR, "cypress/data_fixtures/_build/generated.json"
        )

        call_command(
            "dumpdata",
            output=result_path,
            exclude=[
                "contenttypes",
                "auth",
                "sessions",
                "messages",
                "staticfiles",
                "postgres",
                "admin_index",
            ],
        )
