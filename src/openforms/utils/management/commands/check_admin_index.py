import json
import os

from django.conf import settings
from django.core.management import BaseCommand
from django.test import RequestFactory

from django_admin_index.models import AppGroup

from openforms.accounts.models import User


class Command(BaseCommand):
    help = "Check the admin-index for unregistered models"

    # a whitelist of models explicitly not listed in admin-index
    unlisted_models_fixture = "src/openforms/fixtures/admin_index_unlisted.json"

    def load_unlisted(self):
        unlisted_path = os.path.join(settings.BASE_DIR, self.unlisted_models_fixture)
        with open(unlisted_path) as f:
            return json.load(f)

    def handle(self, **options):
        request = RequestFactory().get("/")
        request.user = User(is_superuser=True)
        results = AppGroup.objects.as_list(request, include_remaining=True)
        unlisted = self.load_unlisted()

        for group in results:
            if group["app_label"] == "misc":
                missing = list()

                for model in group["models"]:
                    label = f"{model['app_label']}.{model['object_name']}"
                    if label not in unlisted:
                        missing.append(model)

                if missing:
                    self.stdout.write(
                        f"Found {len(missing)} models not registered in admin-index:"
                    )
                    for model in missing:
                        self.stdout.write(
                            f"  - {model['app_label']}.{model['object_name']}"
                        )
                    self.stdout.write(
                        f"To show this model on the 'Miscellaneous' tab add it to '{self.unlisted_models_fixture}'"
                    )
                    exit(1)
