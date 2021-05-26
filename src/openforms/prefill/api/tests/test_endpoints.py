from unittest.mock import patch

from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory

from ...contrib.demo.plugin import DemoPrefill
from ...registry import Registry

register = Registry()

register("test")(DemoPrefill)


class AuthTests(APITestCase):

    endpoints = [
        reverse_lazy("api:plugin-list"),
        reverse_lazy("api:attribute-list", kwargs={"plugin": "test"}),
    ]

    def setUp(self):
        super().setUp()

        patcher = patch("openforms.prefill.api.views.register", new=register)
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

        patcher = patch("openforms.prefill.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pefill_list(self):
        endpoint = reverse("api:plugin-list")

        response = self.client.get(endpoint)

        expected = [
            {
                "id": "test",
                "label": _("Demo"),
            }
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    def test_attributes_list(self):
        endpoint = reverse("api:attribute-list", kwargs={"plugin": "test"})

        response = self.client.get(endpoint)

        expected = [
            {
                "id": "random_number",
                "label": _("Random number"),
            },
            {
                "id": "random_string",
                "label": _("Random string"),
            },
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    def test_attributes_invalid_plugin_ids(self):
        invalid = ["demo", 1234, "None"]
        for plugin in invalid:
            with self.subTest(plugin_id=plugin):
                endpoint = reverse("api:attribute-list", kwargs={"plugin": plugin})

                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
