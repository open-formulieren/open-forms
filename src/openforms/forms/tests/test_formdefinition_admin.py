from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.tests.utils import disable_2fa


@disable_2fa
class FormDefinitionAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_formdefinition_list_for_user_with_readonly_perms(self):
        user = StaffUserFactory.create(user_permissions=["view_formdefinition"])

        url = reverse("admin:forms_formdefinition_changelist")
        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)

    def test_formdefinition_list_for_user_with_all_perms(self):
        user = SuperUserFactory.create()
        url = reverse("admin:forms_formdefinition_changelist")
        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)
