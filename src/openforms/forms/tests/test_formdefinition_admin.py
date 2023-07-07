from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.tests.utils import disable_2fa

from ..models.form_definition import FormDefinition
from .factories import FormDefinitionFactory


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

    @override_settings(LANGUAGE_CODE="en")
    def test_copy_with_long_names_succeeds(self):
        user = SuperUserFactory.create()
        FormDefinitionFactory.create(
            name="This is a really long long name for formdefinition",
            internal_name="This is a really long long name for formdefinition",
        )

        self.assertEqual(FormDefinition.objects.count(), 1)

        url = reverse("admin:forms_formdefinition_changelist")
        response = self.app.get(url, user=user)
        form = response.forms["changelist-form"]
        form["action"] = "make_copies"
        form["_selected_action"].checked = True
        response = form.submit("submit", value="0")

        form_definition_copy = FormDefinition.objects.last()

        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertRedirects(response, reverse("admin:forms_formdefinition_changelist"))
        self.assertEqual(
            form_definition_copy.name,
            "This is a really long long name for formde\u2026 (copy)",
        )
        self.assertEqual(
            form_definition_copy.internal_name,
            "This is a really long long name for formde\u2026 (copy)",
        )
