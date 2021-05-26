from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse_lazy
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
