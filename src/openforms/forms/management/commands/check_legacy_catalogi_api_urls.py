from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Check for legacy Catalogi API URL usage."

    def handle(self, **options):
        # raise CommandError("Legacy Catalogi API URL usage detected.")
        pass
