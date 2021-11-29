from django.contrib.auth.models import Permission
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.tests.utils import disable_2fa


@disable_2fa
class FormDefinitionAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_user = UserFactory.create(is_staff=True)
        cls.superuser = SuperUserFactory.create()

    def test_formdefinition_list_for_user_with_readonly_perms(self):
        perm = Permission.objects.get(codename="view_formdefinition")
        self.staff_user.user_permissions.add(perm)

        url = reverse("admin:forms_formdefinition_changelist")
        response = self.app.get(url, user=self.staff_user)

        self.assertEqual(response.status_code, 200)

    def test_formdefinition_list_for_user_with_all_perms(self):
        url = reverse("admin:forms_formdefinition_changelist")
        response = self.app.get(url, user=self.superuser)

        self.assertEqual(response.status_code, 200)
