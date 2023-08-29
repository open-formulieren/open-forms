import zipfile
from pathlib import Path
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time
from privates.storages import private_media_storage
from privates.test import temp_private_root
from rest_framework.exceptions import ValidationError

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.logging.models import TimelineLogProxy
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import (
    activate_forms,
    deactivate_forms,
    process_forms_export,
    process_forms_import,
)
from ...models.form import Form, FormsExport
from ..factories import FormFactory


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class ExportFormsTaskTests(TestCase):
    @freeze_time("2022-02-21T00:00:00")
    def test_zip_file_contains_data(self):
        form1, form2 = FormFactory.create_batch(2)
        user = SuperUserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
        )

        # Test that the forms export model was created with the right data
        forms_exports = FormsExport.objects.all()

        self.assertEqual(1, forms_exports.count())

        forms_export = forms_exports.get()

        self.assertEqual(forms_export.datetime_requested, timezone.now())
        self.assertEqual(user, forms_export.user)

        # Test that the zip file contains the right forms
        with zipfile.ZipFile(forms_export.export_content.path, "r") as file:
            names_list = file.namelist()

        self.assertEqual(2, len(names_list))
        self.assertIn(f"form_{form1.slug}.zip", names_list)
        self.assertIn(f"form_{form2.slug}.zip", names_list)

        # Test that the email has been sent to the user
        sent_mail = mail.outbox[0]

        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": forms_export.uuid},
            )
        )

        self.assertIn(download_url, sent_mail.body)
        self.assertEqual("Forms export ready", sent_mail.subject)
        self.assertIn("test@email.nl", sent_mail.to)


@temp_private_root()
class ImportFormsTaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        form1, form2 = FormFactory.create_batch(2)
        user = SuperUserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
        )

        cls.form_export = FormsExport.objects.get()
        cls.user = user

    def _copy_file_to_imports_tempdir(self):
        exported_zip_file = self.form_export.export_content
        exported_zip_file.seek(0)

        name = "imports/tmp_import_file.zip"
        filename = private_media_storage.save(name, exported_zip_file)

        return filename

    def test_import_forms(self):
        imported_file_path = self._copy_file_to_imports_tempdir()
        process_forms_import(str(imported_file_path), self.user.id)

        self.assertEqual(4, Form.objects.count())

        # Check that no files are left over
        dir_path = Path(private_media_storage.path(imported_file_path)).parent
        self.assertEqual(0, len(list(dir_path.iterdir())))

    @patch(
        "openforms.forms.admin.tasks.import_form",
        side_effect=ValidationError("Something went wrong"),
    )
    def test_import_form_failure(self, m_import_form):
        imported_file_path = self._copy_file_to_imports_tempdir()
        process_forms_import(str(imported_file_path), self.user.id)

        self.assertEqual(2, Form.objects.count())

        logs = TimelineLogProxy.objects.filter(user=self.user, object_id=self.user.id)

        self.assertEqual(1, logs.count())

        log = logs.first()
        failed_forms = log.extra_data["failed_files"]

        self.assertEqual(2, len(failed_forms))

        for item in failed_forms:
            self.assertEqual(item[1], ["Something went wrong"])


class ActivateFormsTests(TestCase):
    @freeze_time("2023-10-10T21:15:00Z")
    def test_forms_are_activated_on_specified_datetime(self):
        form1 = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")
        form2 = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")

        activate_forms()

        form1.refresh_from_db()
        form2.refresh_from_db()

        self.assertTrue(form1.active)
        self.assertIsNone(form1.activate_on)
        self.assertTrue(form2.active)
        self.assertIsNone(form2.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_activation_is_logged(self):
        form = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")

        activate_forms()

        log_entry = TimelineLogProxy.objects.last()
        message = log_entry.get_message()

        self.assertEqual(log_entry.content_object.id, form.id)
        self.assertEqual(
            message.strip().replace("&quot;", '"'),
            f"{log_entry.fmt_lead}: Form was activated.",
        )

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_activated_on_different_time(self):
        form = FormFactory(active=False, activate_on="2023-10-10T21:16:00Z")

        activate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_activated_when_soft_deleted(self):
        form = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")
        form._is_deleted = True
        form.save(update_fields=["_is_deleted"])

        activate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.activate_on)


class DeactivateFormsTests(TestCase):
    @freeze_time("2023-10-10T21:15:00Z")
    def test_forms_are_deactivated_on_specified_datetime(self):
        form1 = FormFactory(deactivate_on="2023-10-10T21:15:00Z")
        form2 = FormFactory(deactivate_on="2023-10-10T21:15:00Z")

        deactivate_forms()

        form1.refresh_from_db()
        form2.refresh_from_db()

        self.assertFalse(form1.active)
        self.assertIsNone(form1.deactivate_on)
        self.assertFalse(form2.active)
        self.assertIsNone(form2.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_deactivation_is_logged(self):
        form = FormFactory(deactivate_on="2023-10-10T21:15:00Z")

        deactivate_forms()

        log_entry = TimelineLogProxy.objects.last()
        message = log_entry.get_message()

        self.assertEqual(log_entry.content_object.id, form.id)
        self.assertEqual(
            message.strip().replace("&quot;", '"'),
            f"{log_entry.fmt_lead}: Form was deactivated.",
        )

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_deactivated_on_different_time(self):
        form = FormFactory(deactivate_on="2023-10-10T21:16:00Z")

        deactivate_forms()

        form.refresh_from_db()

        self.assertTrue(form.active)
        self.assertIsNotNone(form.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_deactivated_when_soft_deleted(self):
        form = FormFactory(active=False, deactivate_on="2023-10-10T21:15:00Z")
        form._is_deleted = True
        form.save(update_fields=["_is_deleted"])

        deactivate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.deactivate_on)
