from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class APIschemaGenerationTests(APITestCase):
    def test_schema_endpoint(self):
        # kitchensink test - request the API schema which should process all (custom)
        # hooks and extensions
        url = reverse("api:api-schema-json")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
