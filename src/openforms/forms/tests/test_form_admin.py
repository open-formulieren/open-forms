from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.registrations.registry import Registry
from openforms.registrations.tests.utils import patch_registry

from ..models import Form

model_field = Form._meta.get_field("registration_backend")

register = Registry()


@register("callback", "A demo callback")
def callback(submission, options):
    pass


class FormAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = SuperUserFactory.create()

    def test_valid_callbacks_listed(self):
        url = reverse("admin:forms_form_add")

        with patch_registry(model_field, register):
            add_page = self.app.get(url, user=self.superuser)

        plugin_field = add_page.form["registration_backend"]
        choices = [(val, label) for val, _, label in plugin_field.options]
        self.assertEqual(
            choices,
            [
                ("", "---------"),
                ("callback", "A demo callback"),
            ],
        )

    def test_create_form_valid_callback(self):
        url = reverse("admin:forms_form_add")

        with patch_registry(model_field, register):
            add_page = self.app.get(url, user=self.superuser)

            add_page.form["name"] = "test form"
            add_page.form["slug"] = "test-form"
            add_page.form["registration_backend"].select("callback")

            resp = add_page.form.submit()

            self.assertEqual(resp.status_code, 302)

        form = Form.objects.get()
        self.assertEqual(form.registration_backend, "callback")

    def test_submit_invalid_value(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:forms_form_add")
        add_page = self.app.get(url, user=self.superuser)

        add_page.form["name"] = "test form"
        add_page.form["slug"] = "test-form"

        body = {
            **dict(add_page.form.submit_fields()),
            "registration_backend": "invalid-backend",
        }

        response = self.client.post(url, body)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "adminform",
            "registration_backend",
            ["Selecteer een geldige keuze. invalid-backend is geen beschikbare keuze."],
        )
