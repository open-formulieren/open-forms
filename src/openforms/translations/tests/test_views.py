from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


class FormioTranslationsEndpointTests(APITestCase):
    def test_returns_translations(self):
        response = self.client.get(reverse("api:translations:formio-translations"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn("nl", response.json())
