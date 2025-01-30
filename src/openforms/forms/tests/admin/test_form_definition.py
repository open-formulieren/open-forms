import json

from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.models import FormDefinition, FormVariable
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


@disable_admin_mfa()
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

    def test_cannot_mark_form_definition_as_non_reusable_if_used_in_multiple_forms(
        self,
    ):
        step = FormStepFactory.create(form_definition__is_reusable=True)
        FormStepFactory.create(form_definition=step.form_definition)

        response = self.app.get(
            reverse(
                "admin:forms_formdefinition_change",
                kwargs={"object_id": step.form_definition.pk},
            ),
        )
        form = response.forms["formdefinition_form"]
        form["is_reusable"] = False
        response = form.submit()

        self.assertInHTML(
            _(
                "This form definition cannot be marked as 'not-reusable' as it is used "
                "in multiple existing forms."
            ),
            str(response.content),
        )

    def test_template_syntax_errors_in_formio_config(self):
        fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "invalidTemplate",
                        "label": "{% bad tag and syntax %}",
                    }
                ]
            }
        )

        change_page = self.app.get(
            reverse("admin:forms_formdefinition_change", kwargs={"object_id": fd.pk}),
        )
        form = change_page.forms["formdefinition_form"]
        assert "{% bad tag and syntax %}" in form["configuration"].value

        # submit the form, which throws validation errors
        submit_response = form.submit()

        self.assertEqual(submit_response.status_code, 200)
        errors = submit_response.context["adminform"].errors
        expected_error = _(
            "The component '{key}' (at JSON path '{path}') has template syntax errors "
            "in the field '{field}'."
        ).format(key="invalidTemplate", path="components.0", field="label")
        self.assertEqual(errors["configuration"], [expected_error])
        self.assertContains(submit_response, expected_error.replace("'", "&#x27;"))

    def test_updating_formio_configuration_fixes_form_variables(self):
        fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "original",
                        "label": "Original",
                    }
                ]
            },
            is_reusable=True,
        )
        fs1, fs2 = FormStepFactory.create_batch(2, form_definition=fd)
        assert fs1.form != fs2.form
        assert fs1.form.formvariable_set.get().key == "original"
        assert fs2.form.formvariable_set.get().key == "original"
        change_page = self.app.get(
            reverse("admin:forms_formdefinition_change", kwargs={"object_id": fd.pk}),
        )
        form = change_page.forms["formdefinition_form"]
        form["configuration"] = json.dumps(
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "updated",
                        "label": "Updated",
                    }
                ]
            }
        )

        form.submit()

        form_vars = FormVariable.objects.filter(form__in=(fs1.form, fs2.form))
        self.assertQuerySetEqual(
            form_vars,
            ["updated", "updated"],
            transform=lambda variable: variable.key,  # type: ignore
            ordered=False,
        )
