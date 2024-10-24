from django.core.management.base import BaseCommand

from openforms.contrib.open_producten.client import get_open_producten_client
from openforms.contrib.open_producten.models import OpenProductenConfig
from openforms.contrib.open_producten.price_import import PriceImporter


class Command(BaseCommand):
    help = "Import product types"

    def handle(self, *args, **options):
        if OpenProductenConfig.objects.count() == 0:
            self.stdout.write(
                "Please define the OpenProductenConfig before running this command."
            )
            return

        client = get_open_producten_client()
        price_importer = PriceImporter(client)

        (
            created,
            updated,
        ) = price_importer.import_product_types()

        self.stdout.write(f"updated {len(updated)} exising product type(s)")
        self.stdout.write(f"created {len(created)} new product type(s):\n")

        for instance in created:
            self.stdout.write(f"{type(instance).__name__}: {instance.uuid}")
