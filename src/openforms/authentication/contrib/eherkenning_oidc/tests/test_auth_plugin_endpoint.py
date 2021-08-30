from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory

from ..models import OpenIDConnectEHerkenningConfig


class eHerkenningOIDCAuthPluginEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = True
        config.oidc_rp_client_id = "testclient"
        config.oidc_rp_client_secret = "secret"
        config.oidc_rp_sign_algo = "RS256"
        config.oidc_rp_scopes_list = ["openid", "kvk"]

        config.oidc_op_jwks_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/certs"
        )
        config.oidc_op_authorization_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth"
        )
        config.oidc_op_token_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/token"
        )
        config.oidc_op_user_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/userinfo"
        )
        config.save()

        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

    def test_plugin_list_eherkenning_oidc_enabled(self):
        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plugin_names = [p["id"] for p in response.data]
        self.assertIn("eherkenning_oidc", plugin_names)

    def test_plugin_list_eherkenning_oidc_not_enabled(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = False
        config.save()

        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plugin_names = [p["id"] for p in response.data]
        self.assertNotIn("eherkenning_oidc", plugin_names)
