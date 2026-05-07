from django.core.management import BaseCommand
from django.db import transaction

from openforms.zgw_urls_migrator import Migrator


class Command(BaseCommand):
    help = "Report or migrate legacy Catalogi API URL usage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-dry-run",
            "--no-dryrun",
            action="store_false",
            dest="dry_run",
            help="Also execute the reported changes",
        )

    def handle(self, **options):
        dry_run = options["dry_run"]
        self.stdout.write(f"Running migrator, dry run: {dry_run}")
        transaction.set_autocommit(False)

        migrator = Migrator(outfile=self.stdout)
        migrator.migrate()

        if dry_run:
            transaction.rollback()
        else:
            transaction.commit()
