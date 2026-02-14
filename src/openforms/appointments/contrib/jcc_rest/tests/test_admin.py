import json
from unittest.mock import patch

from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.tests.cache import clear_caches

from ..constants import FIELD_TO_FORMIO_COMPONENT


@disable_admin_mfa()
class JccRestAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    def test_change_form_context(self):
        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        context = response.context

        self.assertIn("form_mode", context)
        self.assertIn("available_components", context)

    def test_form_has_configuration_components_populated(self):
        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        form = response.forms["jccrestconfig_form"]
        configuration_value = form.fields["configuration"][0].value

        json_components_data = json.loads(configuration_value)

        self.assertEqual(
            json_components_data,
            {"components": list(FIELD_TO_FORMIO_COMPONENT.values())},
        )

    @patch("openforms.appointments.contrib.jcc_rest.forms.CustomerFields")
    def test_form_validation(self, m):
        m.values = ["initial"]

        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        form = response.forms["jccrestconfig_form"]

        form["configuration"].value = json.dumps(
            {"components": [{"type": "textfield", "key": "changed"}]}
        )

        response = form.submit()

        error_items = response.html.select("ul.errorlist li")
        error_texts = [li.text.strip() for li in error_items]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                "Unknown component key for fields: changed. Adding a component or modifying a component's key is not allowed."
                in error
                for error in error_texts
            )
        )
