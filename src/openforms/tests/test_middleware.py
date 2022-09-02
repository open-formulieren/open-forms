from django.test import TestCase

from rest_framework.reverse import reverse

from openforms.middleware import CSRF_TOKEN_HEADER_NAME


class CSRFTokenMiddleware(TestCase):
    def test_csrftoken_in_header_api_endpoint(self):
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CSRF_TOKEN_HEADER_NAME, response.headers)

    def test_csrftoken_not_in_header_root(self):
        response = self.client.get("/")

        self.assertNotIn(CSRF_TOKEN_HEADER_NAME, response.headers)
