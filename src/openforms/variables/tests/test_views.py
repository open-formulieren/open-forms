from unittest.mock import patch

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.forms.models import FormVariable
from openforms.prefill.constants import IdentifierRoles
from openforms.registrations.base import BasePlugin
from openforms.registrations.registry import Registry as RegistrationRegistry
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.registry import Registry as VariableRegistry
from openforms.variables.service import get_static_variables


class GetStaticVariablesViewTest(APITestCase):
    def test_auth_required(self):
        url = reverse(
            "api:variables:static",
        )

        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["view_formvariable"]
        )
        url = reverse(
            "api:variables:static",
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @freeze_time("2021-07-16T21:15:00+00:00")
    def test_get_static_variables(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        url = reverse(
            "api:variables:static",
        )

        self.client.force_authenticate(user=user)

        class DemoNow(BaseStaticVariable):
            name = "Now"
            data_type = FormVariableDataTypes.datetime

            def get_initial_value(self, *args, **kwargs):
                return "2021-07-16T21:15:00+00:00"

        register = VariableRegistry()
        register("now")(DemoNow)

        with patch(
            "openforms.variables.service.static_variables_registry", new=register
        ):
            response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertEqual(1, len(data))
        self.assertEqual(
            {
                "form": None,
                "form_definition": None,
                "name": "Now",
                "key": "now",
                "source": "",
                "service_fetch_configuration": None,
                "prefill_plugin": "",
                "prefill_attribute": "",
                "prefill_identifier_role": IdentifierRoles.main,
                "prefill_options": {},
                "data_type": FormVariableDataTypes.datetime,
                "data_format": "",
                "is_sensitive_data": False,
                "initial_value": "2021-07-16T21:15:00+00:00",
            },
            data[0],
        )


class GetRegistrationPluginVariablesViewTest(APITestCase):
    def test_auth_required(self):
        url = reverse(
            "api:variables:registration",
        )

        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["view_formvariable"]
        )
        url = reverse(
            "api:variables:registration",
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_get_registration_plugin_variable(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        url = reverse(
            "api:variables:registration",
        )

        self.client.force_authenticate(user=user)

        class DemoNow(BaseStaticVariable):
            name = "Now"
            data_type = FormVariableDataTypes.string

            def get_initial_value(self, *args, **kwargs):
                return "demo initial value"

        variables_registry = VariableRegistry()
        variables_registry("now")(DemoNow)

        class DemoRegistrationPlugin(BasePlugin):
            verbose_name = "Demo verbose name"

            def register_submission(self, submission, options):
                pass

            def get_variables(self) -> list[FormVariable]:
                return get_static_variables(variables_registry=variables_registry)

        plugin_registry = RegistrationRegistry()
        plugin_registry("demo")(DemoRegistrationPlugin)

        with patch(
            "openforms.variables.api.views.registration_plugins_registry",
            new=plugin_registry,
        ):
            response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertEqual(1, len(data))
        self.assertEqual(
            {
                "plugin_identifier": "demo",
                "plugin_verbose_name": "Demo verbose name",
                "plugin_variables": [
                    {
                        "form": None,
                        "form_definition": None,
                        "name": "Now",
                        "key": "now",
                        "source": "",
                        "service_fetch_configuration": None,
                        "prefill_plugin": "",
                        "prefill_attribute": "",
                        "prefill_identifier_role": IdentifierRoles.main,
                        "prefill_options": {},
                        "data_type": FormVariableDataTypes.string,
                        "data_format": "",
                        "is_sensitive_data": False,
                        "initial_value": "demo initial value",
                    }
                ],
            },
            data[0],
        )
