from django.core.management import BaseCommand
from django.test import RequestFactory

from django_admin_index.models import AppGroup

from openforms.accounts.models import User


class Command(BaseCommand):
    help = "Check the admin-index for unregistered models"

    def handle(self, **options):
        request = RequestFactory().get("/")
        request.user = User(is_superuser=True)
        results = AppGroup.objects.as_list(request, include_remaining=True)
        for group in results:
            if group["app_label"] == "misc":
                self.stdout.write(
                    f"Found {len(group['models'])} models not registered in admin-index:"
                )
                for model in group["models"]:
                    self.stdout.write(
                        f"  - {model['app_label']}.{model['object_name']}"
                    )
                exit(1)
