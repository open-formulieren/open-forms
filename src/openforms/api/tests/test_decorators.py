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

    def test_api_headers(self):
        response = self.client.get(self.endpoint)
        self.assertIn("Pragma", response.headers)
        self.assertIn("Cache-Control", response.headers)
        self.assertNotIn("Permissions-Policy", response.headers)
        self.assertEqual(response.headers["Pragma"], "no-cache")
        self.assertEqual(
            response.headers["Cache-Control"],
            "no-cache, no-store, max-age=0, must-revalidate",
        )

    @override_settings(
        API_HEADERS={
            "Pragma": "no-cache",
            "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
            "Permissions-Policy": "camera=(self),geolocation=()",
        }
    )
    def test_api_headers_custom_settings(self):
        response = self.client.get(self.endpoint)
        self.assertIn("Pragma", response.headers)
        self.assertIn("Cache-Control", response.headers)
        self.assertIn("Permissions-Policy", response.headers)
        self.assertEqual(response.headers["Pragma"], "no-cache")
        self.assertEqual(
            response.headers["Cache-Control"],
            "no-cache, no-store, max-age=0, must-revalidate",
        )
        self.assertEqual(
            response.headers["Permissions-Policy"], "camera=(self),geolocation=()"
        )
