import zipfile
from datetime import UTC, datetime

from django.core import mail
from django.core.files.storage import storages
from django.test import TestCase, override_settings
from django.urls import reverse

import time_machine
from privates.test import temp_private_root

from openforms.accounts.tests.factories import UserFactory
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import process_forms_export, process_forms_import
from ...import_export.service import FormExportOptions, export_multiple_forms
from ...models import Form, FormsExport
from ..factories import FormFactory


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class ExportFormsTaskTests(TestCase):
    @time_machine.travel("2022-02-21T00:00:00+00:00", tick=False)
    def test_bulk_export_produces_zip_file_with_nested_exports(self):
        form1, form2 = FormFactory.create_batch(2)
        user = UserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
            export_options={},
        )

        # we expect exactly one export record to be created
        forms_export = FormsExport.objects.get()
        self.assertEqual(
            forms_export.datetime_requested, datetime(2022, 2, 21, 0, 0, 0, tzinfo=UTC)
        )
        self.assertEqual(forms_export.user, user)

        with (
            self.subTest("verify export content"),
            forms_export.export_content.open("rb") as content,
            zipfile.ZipFile(content, "r") as zf,
        ):
            expected_names = {
                f"form_{form1.slug}.zip",
                f"form_{form2.slug}.zip",
            }
            self.assertEqual(set(zf.namelist()), expected_names)

        with self.subTest("notification email"):
            self.assertEqual(len(mail.outbox), 1)
            sent_mail = mail.outbox[0]

            download_url = build_absolute_uri(
                reverse(
                    "admin:download_forms_export",
                    kwargs={"uuid": forms_export.uuid},
                )
            )

            self.assertIn(download_url, str(sent_mail.body))
            self.assertEqual("Forms export ready", sent_mail.subject)
            self.assertIn("test@email.nl", sent_mail.to)


@temp_private_root()  # uses an in-memory storage
class ImportFormsTaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()

    def test_task_imports_forms_from_file_storage(self):
        forms = FormFactory.create_batch(2)
        storage = storages["privates"]
        with storage.open("export.zip", "wb") as outfile:
            export_multiple_forms(
                [form.uuid for form in forms],
                export_options=FormExportOptions(),
                target=outfile,
            )

        process_forms_import("export.zip", user_id=self.user.pk, import_options={})

        # 2 pre-existing and those have been imported again
        self.assertEqual(Form.objects.count(), 4)
        self.assertFalse(storage.exists("export.zip"))
