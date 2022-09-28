from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Upgrade test utility, always fails"

    def handle(self, **options):
        raise CommandError("Failed")
