from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _

from ...utils import export_form


class Command(BaseCommand):
    help = "Export form as JSON using the API specification."

    def add_arguments(self, parser):
        parser.add_argument(
            "form_id",
            help=_("ID of the form to be exported"),
            type=int,
        )
        parser.add_argument(
            "archive_name", help=_("Name of the archive to write data to"), type=str
        )

    def handle(self, *args, **options):
        archive_name = options["archive_name"]
        form_id = options["form_id"]

        export_form(form_id, archive_name=archive_name)
