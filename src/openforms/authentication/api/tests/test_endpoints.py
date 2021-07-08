from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory

from ...base import BasePlugin
from ...constants import AuthAttribute
from ...registry import Registry


class NoAuthPlugin(BasePlugin):
    provides_auth = None
    verbose_name = "NoAuthPlugin"


class SingleAuthPlugin(BasePlugin):
    provides_auth = AuthAttribute.bsn
    verbose_name = "SingleAuthPlugin"


class MultiAuthPlugin(BasePlugin):
    provides_auth = [AuthAttribute.bsn, AuthAttribute.kvk]
    verbose_name = "MultiAuthPlugin"


register = Registry()
register("plugin1")(NoAuthPlugin)
register("plugin2")(SingleAuthPlugin)
register("plugin3")(MultiAuthPlugin)


class AuthTests(APITestCase):
    endpoints = [
        reverse_lazy("api:authentication-plugin-list"),
    ]

    def setUp(self):
        super().setUp()

        patcher = patch("openforms.authentication.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_forbidden_not_authenticated(self):
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forbidden_authenticated_but_not_staff(self):
        user = UserFactory.create(is_staff=False)
        self.client.force_authenticate(user=user)

        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_and_staff(self):
        other_user = UserFactory.create(is_staff=True)

        self.client.force_authenticate(user=other_user)

        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, status.HTTP_200_OK)


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

    def test_plugin_list(self):
        endpoint = reverse("api:authentication-plugin-list")

        response = self.client.get(endpoint)

        expected = [
            {
                "id": "plugin1",
                "label": "NoAuthPlugin",
                "providesAuth": [],
            },
            {
                "id": "plugin2",
                "label": "SingleAuthPlugin",
                "providesAuth": ["bsn"],
            },
            {
                "id": "plugin3",
                "label": "MultiAuthPlugin",
                "providesAuth": ["bsn", "kvk"],
            },
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)
