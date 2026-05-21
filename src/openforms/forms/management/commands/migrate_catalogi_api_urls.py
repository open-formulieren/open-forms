from django.core.management import BaseCommand, CommandError
from django.db import transaction

from openforms.zgw_urls_migrator import MigrationProblem, Migrator


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

        migrator = Migrator(outfile=self.stdout)
        try:
            with transaction.atomic():
                migrator.migrate()

                if dry_run:
                    transaction.set_rollback(True)
        except MigrationProblem as exc:
            raise CommandError(exc.message) from exc
