from django.core.management import BaseCommand

from openforms.contrib.microsoft.client import MSGraphClient
from openforms.registrations.contrib.microsoft_graph.models import (
    MSGraphRegistrationConfig,
)


class Command(BaseCommand):
    help = (
        "Display folders and file structure of configured MS Graph registration storage"
    )

    def handle(self, **options):
        config = MSGraphRegistrationConfig.get_solo()
        client = MSGraphClient(config.service)

        storage = client.account.storage()
        drive = storage.get_default_drive()
        root_folder = drive.get_root_folder()

        self.print_folder(root_folder)

    def print_folder(self, folder, level=0):
        items = list(folder.get_items())
        pad = "   " * level
        for item in items:
            if item.is_folder:
                self.stdout.write(pad + item.name)
                self.print_folder(item, level + 1)

        for item in items:
            if item.is_file:
                self.stdout.write(pad + item.name)
