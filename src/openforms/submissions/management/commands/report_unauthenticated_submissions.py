from django.core.management import BaseCommand

from ...models import Submission


class Command(BaseCommand):
    help = "Report the submissions without authentication where the form requires it"

    def handle(self, **options):
        queryset = Submission.objects.filter(
            form__formstep__form_definition__login_required=True,
            auth_info__isnull=True,
        ).values_list("id", "uuid")

        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS("No problematic submissions found."))
            return

        self.stdout.write(
            self.style.ERROR(f"Found {queryset.count()} problematic submission(s):")
        )
        for id, uuid in queryset:
            self.stdout.write(f"- ID: {id} (UUID: {uuid})")
