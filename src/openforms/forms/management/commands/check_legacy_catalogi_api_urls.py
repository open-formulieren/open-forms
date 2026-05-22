from django.core.management import BaseCommand, CommandError

from openforms.zgw_urls_migrator import Migrator


class Command(BaseCommand):
    help = "Check for legacy Catalogi API URL usage."

    def handle(self, **options):
        migrator = Migrator(outfile=self.stdout)
        self.stdout.write("Checking for legacy ZGW API URL usages...")

        check_passes = migrator.check()
        if not check_passes:
            self.stdout.write(
                self.style.WARNING(
                    "Did you forget to run the 'migrate_catalogi_api_urls --no-dry-run'"
                    " migration tool on 3.5?"
                )
            )
            raise CommandError("Legacy Catalogi API URL usage detected.")

        self.stdout.write("Ok, all set!")
