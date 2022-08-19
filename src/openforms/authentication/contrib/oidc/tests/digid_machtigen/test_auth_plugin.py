from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration


class DigiDMachtigenOIDCAuthPluginEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_plugin_list_digid_machtigen_oidc_enabled(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={
                "authentication": {
                    "digid_machtigen_oidc": {"enabled": True},
                },
            }
        )

        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plugin_names = [p["id"] for p in response.data]
        self.assertIn("digid_machtigen_oidc", plugin_names)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_plugin_list_digid_machtigen_oidc_not_enabled(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={
                "authentication": {
                    "digid_machtigen_oidc": {"enabled": False},
                },
            }
        )

        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plugin_names = [p["id"] for p in response.data]
        self.assertNotIn("digid_machtigen_oidc", plugin_names)
