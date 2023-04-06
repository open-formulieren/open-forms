from unittest.mock import patch

from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...base import BasePlugin
from ...registry import Registry

register = Registry()


class TestAttributes(models.TextChoices):
    one = "one_id", "One Label"
    two = "two_id", "Two Label"


class OptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    attribute = serializers.CharField(
        label=_("Example attribute"),
        required=True,
    )


class Plugin(BasePlugin):
    verbose_name = "Test"
    configuration_options = OptionsSerializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result: dict) -> None:
        pass


register("test")(Plugin)


class AuthTests(APITestCase):
    endpoints = [
        reverse_lazy("api:registrations-plugin-list"),
        reverse_lazy("api:registrations-attribute-list"),
    ]

    def setUp(self):
        super().setUp()

        patcher = patch("openforms.registrations.api.views.register", new=register)
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

        patcher = patch("openforms.registrations.api.views.register", new=register)
        patcher.start()
        patcher2 = patch(
            "openforms.registrations.api.views.RegistrationAttribute",
            new=TestAttributes,
        )
        patcher2.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(patcher2.stop)

    def test_plugin_list(self):
        endpoint = reverse("api:registrations-plugin-list")

        response = self.client.get(endpoint)

        expected = [
            {
                "id": "test",
                "label": "Test",
                "schema": {
                    "type": "object",
                    "properties": {
                        "attribute": {
                            "type": "string",
                            "minLength": 1,
                            "title": "Example attribute",
                        }
                    },
                    "required": ["attribute"],
                },
            }
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    def test_attributes_list(self):
        endpoint = reverse("api:registrations-attribute-list")

        response = self.client.get(endpoint)

        expected = [
            {
                "id": "one_id",
                "label": "One Label",
            },
            {
                "id": "two_id",
                "label": "Two Label",
            },
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)


class ListPluginsTests(APITestCase):
    def test_list_plugins(self):
        user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=user)
        endpoint = reverse("api:registrations-plugin-list")

        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
