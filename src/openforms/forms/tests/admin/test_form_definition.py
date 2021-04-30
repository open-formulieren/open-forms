from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.admin import FormDefinitionAdmin
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


class TestFormDefinitionAdmin(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.form_definition = FormDefinitionFactory.create()
        self.form = FormFactory.create()
        self.form_url = reverse(
            "admin:forms_form_change",
            kwargs={"object_id": self.form.pk},
        )
        FormStepFactory.create(form=self.form, form_definition=self.form_definition)
        self.user = SuperUserFactory.create()
        assert self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

    def test_used_in_forms_returns_properly_formatted_html(self):

        result = FormDefinitionAdmin(
            model=self.form_definition, admin_site=AdminSite()
        ).used_in_forms(self.form_definition)

        self.assertEqual(
            result, f"<ul><li><a href={self.form_url}>{self.form.name}</a></li></ul>"
        )

    def test_used_in_forms_shown_in_list_response(self):

        response = self.client.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertIn(
            f"<ul><li><a href={self.form_url}>{self.form.name}</a></li></ul>",
            str(response.content),
        )
