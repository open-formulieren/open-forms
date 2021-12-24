from django.urls import reverse

from django_webtest import WebTest
from rest_framework.serializers import Serializer

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.registrations.registry import Registry
from openforms.registrations.tests.utils import patch_registry
from openforms.tests.utils import disable_2fa

from ...registrations.base import BasePlugin
from ..models import Form
from .factories import FormFactory

model_field = Form._meta.get_field("registration_backend")

register = Registry()


class OptionsSerializer(Serializer):
    pass


@register("plugin")
class Plugin(BasePlugin):
    verbose_name = "A demo plugin"
    configuration_options = OptionsSerializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result) -> str:
        return "foo"


@disable_2fa
class FormAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = SuperUserFactory.create()

    def test_form_list_view_hides_soft_deleted(self):
        form_visible = FormFactory.create(active=True)
        FormFactory.create(deleted_=True)

        url = reverse("admin:forms_form_changelist")
        response = self.app.get(url, user=self.superuser, status=200)

        visible = list(response.context["cl"].result_list.all())
        self.assertEqual(visible, [form_visible])

    def test_form_list_view_delete_action_soft_deletes(self):
        form_delete = FormFactory.create()
        form_keep = FormFactory.create()

        url = reverse("admin:forms_form_changelist")
        response = self.app.get(url, user=self.superuser, status=200)

        form = response.forms["changelist-form"]
        form["action"] = "delete_selected"
        form["_selected_action"] = [str(form_delete.pk)]

        response = form.submit(status=200)

        # deletion confirmation
        response.form.submit()

        form_delete.refresh_from_db()
        form_keep.refresh_from_db()

        self.assertTrue(form_delete._is_deleted)
        self.assertFalse(form_keep._is_deleted)

    def test_form_change_view_hides_soft_deleted(self):
        form = FormFactory.create(deleted_=True)

        url = reverse("admin:forms_form_change", kwargs={"object_id": form.id})
        response = self.app.get(url, user=self.superuser)
        # admin redirects instead of 404 when instance not found
        self.assertEqual(response.status_code, 302)

    def test_form_change_view_delete_action_soft_deletes(self):
        form = FormFactory.create()

        url = reverse("admin:forms_form_delete", kwargs={"object_id": form.id})
        response = self.app.get(url, user=self.superuser)

        # deletion confirmation
        response.form.submit()

        form.refresh_from_db()
        self.assertTrue(form._is_deleted)


@disable_2fa
class FormAdminNonReactTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = SuperUserFactory.create()

        config = GlobalConfiguration.get_solo()
        config.enable_react_form = False
        config.save()

    def test_valid_plugins_listed(self):
        url = reverse("admin:forms_form_add")

        with patch_registry(model_field, register):
            add_page = self.app.get(url, user=self.superuser)

        plugin_field = add_page.form["registration_backend"]
        choices = [(val, label) for val, _, label in plugin_field.options]
        self.assertEqual(
            choices,
            [
                ("", "---------"),
                ("plugin", "A demo plugin"),
            ],
        )

    def test_create_form_valid_plugin(self):
        url = reverse("admin:forms_form_add")

        with patch_registry(model_field, register):
            add_page = self.app.get(url, user=self.superuser)

            add_page.form["name"] = "test form"
            add_page.form["internal_name"] = "internal form"
            add_page.form["slug"] = "test-form"
            add_page.form["registration_backend"].select("plugin")

            resp = add_page.form.submit()

            self.assertEqual(resp.status_code, 302)

        form = Form.objects.get()
        self.assertEqual(form.registration_backend, "plugin")

    def test_submit_invalid_value(self):
        self.app.set_user(self.superuser)
        url = reverse("admin:forms_form_add")
        add_page = self.app.get(url, user=self.superuser)

        add_page.form["name"] = "test form"
        add_page.form["slug"] = "test-form"

        body = {
            **dict(add_page.form.submit_fields()),
            "registration_backend": "invalid-backend",
        }

        response = self.app.post(url, body)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "adminform",
            "registration_backend",
            ["Selecteer een geldige keuze. invalid-backend is geen beschikbare keuze."],
        )
