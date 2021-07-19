from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory


class FormVersionAdminImportExportTests(WebTest):
    def setUp(self):
        self.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_form(self):
        response = self.app.get(
            reverse("admin:forms_formversion_add"), user=self.user, status=403
        )

        self.assertEqual(403, response.status_code)
