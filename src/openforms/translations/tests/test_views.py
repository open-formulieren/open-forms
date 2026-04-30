from django.conf import settings
from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .factories import TranslationsMetaDataFactory


@override_settings(SENDFILE_BACKEND="django_sendfile.backends.nginx")
class CustomizedCompiledTranslationsTests(APITestCase):
    def test_view_returns_compiled_file_json_data(self):
        TranslationsMetaDataFactory.create(language_code="en", with_compiled_asset=True)

        endpoint = reverse("api:i18n:customized-translations", args=["en"])
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.headers["Content-Type"], "application/json")

        # make sure nginx serves the file directly via the private media directory
        self.assertTrue(
            response.headers["X-Accel-Redirect"].startswith(settings.PRIVATE_MEDIA_URL)
        )
        self.assertIn("compiled_test_en", response.headers["X-Accel-Redirect"])

    def test_returns_empty_object_when_no_compiled_asset_found(self):
        endpoint = reverse(
            "api:i18n:customized-translations", kwargs={"language_code": "nl"}
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})
        self.assertNotIn("X-Accel-Redirect", response)

    def test_view_when_language_unsupported(self):
        endpoint = reverse("api:i18n:customized-translations", args=["gr"])
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
