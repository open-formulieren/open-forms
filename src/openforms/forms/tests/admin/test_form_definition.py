from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.models import FormDefinition
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.tests.utils import disable_2fa


@disable_2fa
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
        self.user = SuperUserFactory.create(app=self.app)
        self.app.set_user(self.user)

    def test_used_in_forms_shown_in_list_response(self):

        response = self.app.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertInHTML(
            f'<ul><li><a href="{self.form_url}">{self.form.admin_name}</a></li></ul>',
            str(response.content),
        )

    def test_used_in_forms_when_form_has_user_input_properly_escaped(self):
        form = FormFactory.create(name="<script>alert('foo')</script>")
        FormStepFactory.create(form=form, form_definition=self.form_definition)

        response = self.app.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertInHTML(
            "&lt;script&gt;alert(&#39;foo&#39;)&lt;/script&gt;",
            str(response.content),
        )

    def test_used_in_forms_shows_forms_for_each_for_each_form_definition_without_duplicates(
        self,
    ):
        second_form_definition = FormDefinitionFactory.create()
        second_form = FormFactory.create()
        second_form_url = reverse(
            "admin:forms_form_change",
            kwargs={"object_id": second_form.pk},
        )

        FormStepFactory.create(form=self.form, form_definition=second_form_definition)
        FormStepFactory.create(form=second_form, form_definition=self.form_definition)
        FormStepFactory.create(form=second_form, form_definition=second_form_definition)

        # Duplicate steps
        FormStepFactory.create(form=self.form, form_definition=second_form_definition)
        FormStepFactory.create(form=second_form, form_definition=second_form_definition)
        self.client.force_login(user=self.user)

        response = self.client.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertInHTML(
            f'<li><a href="{self.form_url}">{self.form.admin_name}</a></li>',
            str(response.content),
            count=2,
        )
        self.assertInHTML(
            f'<li><a href="{second_form_url}">{second_form.admin_name}</a></li>',
            str(response.content),
            count=2,
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
        self.assertEqual(
            copied_form.name, _("{name} (copy)").format(name=self.form_definition.name)
        )
        self.assertEqual(
            copied_form.slug, _("{slug}-copy").format(slug=self.form_definition.slug)
        )

    def test_deleted_forms_not_in_used_in(self):
        form_definition = FormDefinitionFactory.create()
        deleted_form = FormFactory.create(deleted_=True)
        deleted_form_url = reverse(
            "admin:forms_form_change",
            kwargs={"object_id": deleted_form.pk},
        )
        active_form = FormFactory.create()
        active_form_url = reverse(
            "admin:forms_form_change",
            kwargs={"object_id": active_form.pk},
        )

        FormStepFactory.create(form=deleted_form, form_definition=form_definition)
        FormStepFactory.create(form=active_form, form_definition=form_definition)

        response = self.app.get(reverse("admin:forms_formdefinition_changelist"))

        self.assertInHTML(
            f'<li><a href="{active_form_url}">{active_form.admin_name}</a></li>',
            str(response.content),
        )
        self.assertNotIn(
            deleted_form_url,
            str(response.content),
        )
