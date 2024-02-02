from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormVariableFactory


@disable_admin_mfa()
class FormVariableAdminTest(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_can_delete_variable(self):
        variable = FormVariableFactory.create()
        admin_url = reverse("admin:forms_formvariable_change", args=(variable.pk,))

        response = self.app.get(admin_url, user=self.user)

        html = response.html
        delete_button = html.find_all("a", class_="deletelink")

        self.assertEqual(1, len(delete_button))
        self.assertEqual(
            delete_button[0].attrs["href"],
            reverse("admin:forms_formvariable_delete", args=(variable.pk,)),
        )
