from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from ...models.form import FormsExport


class Command(BaseCommand):
    help = "Clear the downloaded form export files to free up disk space"

    def handle(self, *args, **options):
        before_date = (
            timezone.now() - timedelta(days=settings.FORMS_EXPORT_REMOVED_AFTER_DAYS)
        ).date()

        forms_exports = FormsExport.objects.filter(
            downloaded=True, date_downloaded__lt=before_date
        )

        for forms_export in forms_exports:
            forms_export.delete()
