from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class NeverCacheAPIEndpointTests(APITestCase):
    def test_response_api_headers(self):
        # grab the ping endpoint as a "random" endpoint
        response = self.client.get(reverse("api:ping"))

        self.assertIn("Pragma", response.headers)
        self.assertIn("Cache-Control", response.headers)
        self.assertNotIn("Permissions-Policy", response.headers)
        self.assertEqual(response.headers["Pragma"], "no-cache")
        self.assertEqual(
            response.headers["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )
