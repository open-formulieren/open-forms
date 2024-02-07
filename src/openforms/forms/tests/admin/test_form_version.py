from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory


@disable_admin_mfa()
class FormVersionAdminImportExportTests(WebTest):
    def setUp(self):
        self.user = SuperUserFactory.create()

    def test_form(self):
        response = self.app.get(
            reverse("admin:forms_formversion_add"), user=self.user, status=403
        )

        self.assertEqual(403, response.status_code)
