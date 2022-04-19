from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from ...models.form import FormsExport


class Command(BaseCommand):
    help = "Clear the downloaded form export files to free up disk space"

    def handle(self, *args, **options):
        before_date = timezone.now() - timedelta(
            days=settings.FORMS_EXPORT_REMOVED_AFTER_DAYS
        )

        forms_exports = FormsExport.objects.filter(datetime_downloaded__lt=before_date)
        forms_exports.delete()
