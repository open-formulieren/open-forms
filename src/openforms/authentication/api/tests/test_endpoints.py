from unittest.mock import patch

from django.db.models import TextChoices
from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.utils.tests.feature_flags import enable_feature_flag

from ...base import BasePlugin
from ...constants import AuthAttribute
from ...registry import Registry


class SingleLoA(TextChoices):
    low = ("low", "low")
    mordac = ("∞", "Stare into the Sun")


class SingleAuthPlugin(BasePlugin):
    provides_auth = AuthAttribute.bsn
    verbose_name = "SingleAuthPlugin"
    assurance_levels = SingleLoA


class DemoAuthPlugin(BasePlugin):
    provides_auth = AuthAttribute.bsn
    verbose_name = "DemoAuthPlugin"
    is_demo_plugin = True


register = Registry()
register("plugin1")(SingleAuthPlugin)
register("plugin2")(DemoAuthPlugin)


class AuthTests(APITestCase):
    endpoint = reverse_lazy("api:authentication-plugin-list")

    def setUp(self):
        super().setUp()

        patcher = patch("openforms.authentication.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_forbidden_not_authenticated(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forbidden_authenticated_but_not_staff(self):
        user = UserFactory.create(is_staff=False)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_and_staff(self):
        other_user = UserFactory.create(is_staff=True)

        self.client.force_authenticate(user=other_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(SOLO_CACHE=None)
class ResponseTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

        patcher = patch("openforms.authentication.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_single_auth_plugin(self):
        endpoint = reverse("api:authentication-plugin-list")
        response = self.client.get(endpoint)

        expected = [
            {
                "id": "plugin1",
                "label": "SingleAuthPlugin",
                "providesAuth": "bsn",
                "supportsLoaOverride": False,
                "assuranceLevels": [
                    {"label": "low", "value": "low"},
                    {"label": "Stare into the Sun", "value": "∞"},
                ],
            }
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_demo_plugin(self):
        endpoint = reverse("api:authentication-plugin-list")
        response = self.client.get(endpoint)

        expected = [
            {
                "id": "plugin1",
                "label": "SingleAuthPlugin",
                "providesAuth": "bsn",
                "supportsLoaOverride": False,
                "assuranceLevels": [
                    {"label": "low", "value": "low"},
                    {"label": "Stare into the Sun", "value": "∞"},
                ],
            },
            {
                "id": "plugin2",
                "label": "DemoAuthPlugin",
                "providesAuth": "bsn",
                "supportsLoaOverride": False,
                "assuranceLevels": [],
            },
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    def test_disabled_plugins_are_not_returned(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "authentication": {"plugin1": {"enabled": False}},
        }
        config.save()
        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
