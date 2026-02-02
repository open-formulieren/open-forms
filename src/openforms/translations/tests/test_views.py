import json

from django.conf import settings
from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .factories import TranslationsMetaDataFactory


class FormioTranslationsEndpointTests(APITestCase):
    # TODO: deprecated, remove when the deprecated view is removed
    def test_returns_translations(self):
        response = self.client.get(reverse("api:translations:formio-translations"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn("nl", response.json())

    def test_language_code_param(self):
        endpoint = reverse("api:i18n:formio-translations", kwargs={"language": "nl"})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        content = b"".join(x for x in response.streaming_content)  # pyright: ignore [reportAttributeAccessIssue]
        translations = json.loads(content)
        self.assertNotIn("nl", translations)
        self.assertGreater(len(translations), 0, "No Dutch translations returned")

    def test_unsupported_language_code(self):
        endpoint = reverse("api:i18n:formio-translations", kwargs={"language": "sw"})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_all_supported_languages_present(self):
        for code, language in settings.LANGUAGES:
            with self.subTest(language=language, code=code):
                endpoint = reverse(
                    "api:i18n:formio-translations", kwargs={"language": code}
                )

                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, status.HTTP_200_OK)


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
