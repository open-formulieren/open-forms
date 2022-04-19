from datetime import date

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.accounts.tests.factories import StaffUserFactory

from ..admin.tasks import process_forms_export
from ..models.form import FormsExport
from .factories import FormFactory


@temp_private_root()
@override_settings(FORMS_EXPORT_REMOVED_AFTER_DAYS=7)
class DeleteFormExportFilesTest(TestCase):
    def test_forms_export_files_deleted(self):
        """
        Assert that when a submission is deleted, the file uploads (on disk!) are deleted.
        """
        form1, form2 = FormFactory.create_batch(2)
        user = StaffUserFactory.create(username="testuser")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            email="test@email.nl",
            user_id=user.id,
        )

        forms_export = FormsExport.objects.get()
        with freeze_time("2022-01-01T00:00:00Z"):
            forms_export.datetime_downloaded = timezone.now()
            forms_export.save()
        path = forms_export.export_content.path
        storage = forms_export.export_content.storage

        with freeze_time("2022-01-09T00:00:00Z"):
            with capture_on_commit_callbacks(execute=True):
                call_command("delete_export_files")

        self.assertFalse(FormsExport.objects.filter(pk=forms_export.pk).exists())
        self.assertFalse(storage.exists(path))
