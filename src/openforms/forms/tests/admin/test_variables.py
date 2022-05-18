from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.constants import FormVariableSources
from openforms.forms.tests.factories import FormVariableFactory


class FormVariableAdminTest(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_cant_delete_static_variable(self):
        variable = FormVariableFactory.create(source=FormVariableSources.static)
        admin_url = reverse("admin:forms_formvariable_change", args=(variable.pk,))

        response = self.app.get(admin_url, user=self.user)

        html = response.html
        delete_button = html.find_all("a", class_="deletelink")

        self.assertEqual(0, len(delete_button))

    def test_cant_delete_component_variable(self):
        variable = FormVariableFactory.create(source=FormVariableSources.component)
        admin_url = reverse("admin:forms_formvariable_change", args=(variable.pk,))

        response = self.app.get(admin_url, user=self.user)

        html = response.html
        delete_button = html.find_all("a", class_="deletelink")

        self.assertEqual(0, len(delete_button))

    def test_can_delete_user_defined_variable(self):
        variable = FormVariableFactory.create(source=FormVariableSources.user_defined)
        admin_url = reverse("admin:forms_formvariable_change", args=(variable.pk,))

        response = self.app.get(admin_url, user=self.user)

        html = response.html
        delete_button = html.find_all("a", class_="deletelink")

        self.assertEqual(1, len(delete_button))
        self.assertEqual(
            delete_button[0].attrs["href"],
            reverse("admin:forms_formvariable_delete", args=(variable.pk,)),
        )
