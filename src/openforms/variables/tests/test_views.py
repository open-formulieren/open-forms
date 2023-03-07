from unittest.mock import patch

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.registry import Registry

from .factories import ServiceFetchConfigurationFactory


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

        register = Registry()
        register("now")(DemoNow)

        with patch("openforms.variables.service.register", new=register):
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
                "data_type": FormVariableDataTypes.datetime,
                "data_format": "",
                "is_sensitive_data": False,
                "initial_value": "2021-07-16T21:15:00+00:00",
            },
            data[0],
        )


class ServiceFetchConfigurationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

    def test_service_fetch_configuration_list_is_forbidden_for_normal_users(self):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_fetch_configuration_list_returns_a_list_to_admin_users(self):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {"count": 0, "next": None, "previous": None, "results": []}
        )

    def test_service_fetch_configuration_have_the_right_properties(self):
        expected_config = ServiceFetchConfigurationFactory.create(
            name="Service fetch configuration 1"
        )
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        config = response.data["results"][0]
        self.assertEqual(
            config["url"], f"http://testserver{endpoint}/{expected_config.pk}"
        )
        self.assertEqual(config["name"], "Service fetch configuration 1")
