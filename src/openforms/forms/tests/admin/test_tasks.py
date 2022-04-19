import zipfile
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from privates.test import temp_private_root

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import process_forms_export
from ...models.form import FormsExport
from ..factories import FormFactory


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class ExportFormsTaskTests(TestCase):
    @patch(
        "openforms.forms.admin.tasks.exported_forms_token_generator.make_token",
        return_value="123-123-123",
    )
    def test_zip_file_contains_data(self, m_token):
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

        self.assertIsNone(forms_export.datetime_downloaded)
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
                kwargs={"pk": forms_export.pk, "token": "123-123-123"},
            )
        )

        self.assertIn(download_url, sent_mail.body)
        self.assertEqual("Forms export ready", sent_mail.subject)
        self.assertIn("test@email.nl", sent_mail.to)
