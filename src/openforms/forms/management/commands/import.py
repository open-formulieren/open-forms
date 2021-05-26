from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError

from ...utils import import_form


class Command(BaseCommand):
    help = "Import form from a ZIP-file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--import-file",
            type=str,
            help=_("The name of the ZIP-file to import from"),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        import_file = options["import_file"]

        try:
            import_form(import_file)
        except ValidationError as e:
            raise CommandError(e) from e
