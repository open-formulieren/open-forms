import io
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.forms.admin.tokens import exported_forms_token_generator
from openforms.forms.models.form import FormsExport
from openforms.forms.tests.factories import FormFactory
from openforms.utils.urls import build_absolute_uri


@override_settings(LANGUAGE_CODE="en")
class TestExportFormsView(WebTest):
    def test_not_staff_cant_access(self):
        user = UserFactory(is_staff=False, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(302, response.status_code)

    def test_staff_cant_access(self):
        user = UserFactory(is_staff=True, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(403, response.status_code)

    def test_no_forms_uuids_specified(self):
        user = SuperUserFactory.create()

        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        form["email"] = "test@email.nl"
        submission_response = form.submit()

        # Doesn't redirect because there are errors
        self.assertEqual(200, submission_response.status_code)

    def test_wrong_form_uuids(self):
        user = SuperUserFactory.create()

        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        form["email"] = "test@email.nl"
        form["forms_uuids"] = "5cd503bf-e83f-4fd1-9acd-c2e8975ff65d"
        submission_response = form.submit()

        # Doesn't redirect because there are errors
        self.assertEqual(200, submission_response.status_code)

    @patch("openforms.forms.admin.views.process_forms_export.delay")
    def test_success_message(self, m):
        form = FormFactory.create()
        user = SuperUserFactory.create()
        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        page_form = response.form
        page_form["forms_uuids"] = str(form.uuid)
        page_form["email"] = "test@email.nl"
        submission_response = page_form.submit()

        self.assertRedirects(
            submission_response, reverse("admin:forms_form_changelist")
        )
        m.assert_called_with(
            forms_uuids=[form.uuid], user_id=user.id, email="test@email.nl"
        )

        submission_response = submission_response.follow()
        messages = list(submission_response.context.get("messages"))

        self.assertEqual(1, len(messages))
        self.assertEqual(messages[0].tags, "success")


@temp_private_root()
class TestDownloadExportFormView(TestCase):
    def test_not_logged_in_cant_access(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export", kwargs={"pk": 1, "token": "123-123-123"}
            )
        )

        response = self.client.get(download_url)

        self.assertEqual(302, response.status_code)

    def test_not_superuser_cant_access(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export", kwargs={"pk": 1, "token": "123-123-123"}
            )
        )

        user = UserFactory(is_staff=True, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(download_url)

        self.assertEqual(403, response.status_code)

    @patch(
        "openforms.forms.admin.tasks.exported_forms_token_generator.check_token",
        return_value=False,
    )
    def test_wrong_token_cant_access(self, m_token):
        user = SuperUserFactory.create(email="test@email.nl")
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user,
        )
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"pk": forms_export.pk, "token": "123-123-123"},
            )
        )

        self.client.force_login(user)
        response = self.client.get(download_url)

        self.assertEqual(403, response.status_code)

    def test_wrong_export_gives_404(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export", kwargs={"pk": 1, "token": "123-123-123"}
            )
        )

        user = SuperUserFactory.create(email="test@email.nl")
        self.client.force_login(user)
        response = self.client.get(download_url)

        self.assertEqual(404, response.status_code)

    @patch(
        "openforms.forms.admin.tasks.exported_forms_token_generator.check_token",
        return_value=True,
    )
    @freeze_time("2022-02-21T00:00:00")
    def test_after_download_export_is_marked_as_downloaded(self, m_token):
        user = SuperUserFactory(email="test@email.nl")
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user,
        )
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"pk": forms_export.pk, "token": "123-123-123"},
            )
        )

        self.client.force_login(user)
        response = self.client.get(download_url)

        self.assertEqual(200, response.status_code)

        forms_export.refresh_from_db()

        self.assertEqual(
            timezone.now(),
            forms_export.datetime_downloaded,
        )

    def test_token(self):
        user = SuperUserFactory(email="test@email.nl")
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user,
        )

        token = exported_forms_token_generator.make_token(forms_export)

        forms_export.datetime_downloaded = timezone.now()
        forms_export.save()

        is_valid = exported_forms_token_generator.check_token(forms_export, token)

        self.assertFalse(is_valid)

    @patch(
        "openforms.forms.admin.tasks.exported_forms_token_generator.check_token",
        return_value=False,
    )
    def test_wrong_user_cant_download(self, m_token):
        user1 = SuperUserFactory(email="test1@email.nl")
        user2 = SuperUserFactory(email="test2@email.nl")
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user1,
        )
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"pk": forms_export.pk, "token": "123-123-123"},
            )
        )

        self.client.force_login(user2)
        response = self.client.get(download_url)

        self.assertEqual(404, response.status_code)
