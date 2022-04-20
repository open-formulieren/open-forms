import zipfile

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import process_forms_export
from ...models.form import FormsExport
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
            email="test@email.nl",
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
        self.assertIn(f"form_{form1.uuid}.zip", names_list)
        self.assertIn(f"form_{form2.uuid}.zip", names_list)

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
