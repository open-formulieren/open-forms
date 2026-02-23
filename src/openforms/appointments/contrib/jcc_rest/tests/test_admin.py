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

    def test_form_has_configuration_components_populated(self):
        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        form = response.forms["jccrestconfig_form"]
        configuration_value = form.fields["configuration"][0].value

        actual_keys = set(
            c["key"] for c in json.loads(configuration_value)["components"]
        )
        expected_keys = set(FIELD_TO_FORMIO_COMPONENT.keys())

        self.assertEqual(actual_keys, expected_keys)

    @patch("openforms.appointments.contrib.jcc_rest.forms.CustomerFields")
    def test_form_validation_with_missing_keys(self, m):
        m.values = ["initial", "another"]

        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        form = response.forms["jccrestconfig_form"]

        form["configuration"].value = json.dumps(
            {"components": [{"type": "textfield", "key": "initial"}]}
        )

        response = form.submit()

        error_items = response.html.select("ul.errorlist li")
        error_texts = [li.text.strip() for li in error_items]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            error_texts[1],
            "Required keys are missing: another.",
        )

    @patch("openforms.appointments.contrib.jcc_rest.forms.CustomerFields")
    def test_form_validation_with_modified_keys(self, m):
        m.values = ["initial"]

        user = SuperUserFactory.create()
        endpoint = reverse("admin:jcc_rest_jccrestconfig_change")
        response = self.app.get(endpoint, user=user)
        form = response.forms["jccrestconfig_form"]

        form["configuration"].value = json.dumps(
            {"components": [{"type": "textfield", "key": "another"}]}
        )

        response = form.submit()

        error_items = response.html.select("ul.errorlist li")
        error_texts = [li.text.strip() for li in error_items]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            error_texts[1],
            "Unknown component keys: another.\nRequired keys are missing: initial.",
        )
