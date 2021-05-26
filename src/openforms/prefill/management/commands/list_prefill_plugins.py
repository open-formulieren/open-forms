from django.core.management import BaseCommand

from ...registry import register


class Command(BaseCommand):
    help = "List the registered prefill plugins"

    def handle(self, **options):
        self.stdout.write("Available plugins:")

        for plugin in register:
            self.stdout.write(
                f"  {plugin.identifier} ({plugin.verbose_name})",
                self.style.MIGRATE_LABEL,
            )
            for attr, label in plugin.get_available_attributes():
                self.stdout.write(f"  * {attr} ({label})")
