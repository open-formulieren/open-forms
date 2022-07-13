from django.test import override_settings

from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory


class DecoratorTests(APITestCase):
    endpoint = reverse_lazy("api:ping")

    def setUp(self) -> None:
        super().setUp()
        self.user = StaffUserFactory.create()
        self.client.force_authenticate(user=self.user)

    def test_response_api_headers(self):
        response = self.client.get(self.endpoint)
        self.assertIn("Pragma", response.headers)
        self.assertIn("Cache-Control", response.headers)
        self.assertNotIn("Permissions-Policy", response.headers)
        self.assertEqual(response.headers["Pragma"], "no-cache")
        self.assertEqual(
            response.headers["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )
