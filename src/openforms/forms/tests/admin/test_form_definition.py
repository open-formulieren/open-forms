from django.http import HttpRequest
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.models import FormDefinition
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


class TestFormDefinitionAdmin(WebTest):
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

    def test_used_in_forms_shown_in_list_response(self):

        response = self.client.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertIn(
            f"<ul><li><a href={self.form_url}>{self.form.name}</a></li></ul>",
            str(response.content),
        )

    def test_make_copies_action_makes_copy_of_a_form_definition(self):
        response = self.app.get(
            reverse("admin:forms_formdefinition_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "make_copies"
        form["_selected_action"] = [
            str(form_definition.pk) for form_definition in FormDefinition.objects.all()
        ]
        form.submit()

        self.assertEqual(FormDefinition.objects.count(), 2)
        copied_form = FormDefinition.objects.exclude(pk=self.form_definition.pk).first()
        self.assertEqual(copied_form.name, f"{self.form_definition.name} (kopie)")
        self.assertEqual(copied_form.slug, f"{self.form_definition.slug}-kopie")
