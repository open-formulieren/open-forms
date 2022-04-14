from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from furl import furl

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.forms.tests.factories import FormFactory


@override_settings(LANGUAGE_CODE="en")
class TestExportFormsView(WebTest):
    def test_not_staff_cant_access(self):
        user = UserFactory(is_staff=False, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(302, response.status_code)

    def test_staff_can_access(self):
        user = UserFactory(is_staff=True, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(200, response.status_code)

    def test_no_forms_uuids_specified(self):
        user = SuperUserFactory.create()

        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        form["email"] = "test@email.nl"
        form["username"] = user.username
        submission_response = form.submit()

        self.assertEqual(200, submission_response.status_code)

        errors = submission_response.html.find("ul", class_="errorlist")

        self.assertIsNotNone(errors)
        self.assertEqual(1, len(errors.contents))
        self.assertEqual(
            "(Hidden field forms_uuids) This field is required.",
            errors.contents[0].text,
        )

    def test_wrong_form_uuids(self):
        user = SuperUserFactory.create()

        export_page = furl(reverse("admin:forms_export"))
        export_page.args["forms_uuids"] = "5cd503bf-e83f-4fd1-9acd-c2e8975ff65d"

        response = self.app.get(export_page.url, user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        form["email"] = "test@email.nl"
        submission_response = form.submit()

        self.assertEqual(200, submission_response.status_code)

        errors = submission_response.html.find("ul", class_="errorlist")

        self.assertIsNotNone(errors)
        self.assertEqual(1, len(errors.contents))
        self.assertEqual(
            "(Hidden field forms_uuids) Invalid form uuids.", errors.contents[0].text
        )

    @patch("openforms.forms.admin.views.process_forms_export.delay")
    def test_success_message(self, m):
        form = FormFactory.create()

        user = SuperUserFactory.create(username="testuser")

        export_page = furl(reverse("admin:forms_export"))
        export_page.args["forms_uuids"] = str(form.uuid)

        response = self.app.get(export_page.url, user=user)

        self.assertEqual(200, response.status_code)

        page_form = response.form
        page_form["email"] = "test@email.nl"
        submission_response = page_form.submit()

        self.assertRedirects(
            submission_response, reverse("admin:forms_form_changelist")
        )
        m.assert_called_with(forms_uuids=[form.uuid], email="test@email.nl")

        submission_response = submission_response.follow()
        messages = list(submission_response.context.get("messages"))

        self.assertEqual(1, len(messages))
        self.assertEqual(messages[0].tags, "success")
