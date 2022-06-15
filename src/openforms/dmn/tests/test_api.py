from typing import Dict
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory

from ..base import BasePlugin, DecisionDefinition
from ..registry import Registry

register = Registry()


@register("test")
class TestPlugin(BasePlugin):
    @staticmethod
    def get_available_decision_definitions():
        return [DecisionDefinition(identifier="test-1", label="Test definition")]

    @staticmethod
    def evaluate(
        definition_id, *, version: str = "", input_values: Dict[str, int]
    ) -> Dict[str, int]:
        return {"sum": sum([input_values["a"], input_values["b"]])}


class MockRegistryMixin:
    def setUp(self):
        super().setUp()

        patcher = patch("openforms.dmn.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)


class AccessControlTests(MockRegistryMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

    def test_plugin_list(self):
        endpoint = reverse("api:dmn-plugin-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_list(self):
        endpoint = reverse("api:dmn-definition-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_version_list(self):
        endpoint = reverse("api:dmn-definition-version-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_xml(self):
        endpoint = reverse("api:dmn-definition-xml", kwargs={"definition": "test-1"})

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
