import json

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.test import APITestCase

from ..constants import StatusChoices
from .factories import TranslationsMetaDataFactory


@override_settings(
    LANGUAGE_CODE="en",
    LANGUAGES=[
        ("en", _("English")),
        ("nl", _("Dutch")),
    ],
)
class I18NAPITests(APITestCase):
    def test_info_contains_available_languages(self):
        # expect language names in their local representation
        url = reverse("api:i18n:info")

        response = self.client.get(url)

        available = response.json()["languages"]
        self.assertEqual(
            available,
            [
                {"code": "en", "name": "English"},
                {"code": "nl", "name": "Nederlands"},
            ],
        )

    def test_info_contains_active_language(self):
        # default fallback
        url = reverse("api:i18n:info")

        response = self.client.get(url)
        current = response.json()["current"]

        self.assertEqual(current, "en")

    def test_info_negotiates_active_language_from_header(self):
        url = reverse("api:i18n:info")

        response = self.client.get(
            url, HTTP_ACCEPT_LANGUAGE="nl-NL, nl;q=0.9, en;q=0.8"
        )

        current = response.json()["current"]
        self.assertEqual(current, "nl")

    def test_put_overrides_negotiated_current(self):
        assert settings.USE_I18N, "Internationalization must be enabled in this project"
        url = reverse("api:i18n:language")

        # set desired to en, with a browser that wants nl
        response = self.client.put(
            url, data={"code": "en"}, HTTP_ACCEPT_LANGUAGE="nl-NL, nl;q=0.9, en;q=0.8"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        # assert current has changed
        current = self.client.get(
            reverse("api:i18n:info"),
            HTTP_ACCEPT_LANGUAGE="nl-NL, nl;q=0.9, en;q=0.8",
        ).json()["current"]
        self.assertEqual(current, "en")

    def test_put_language_checks_for_availability(self):
        url = reverse("api:i18n:language")

        # ትግርኛ is not available
        response = self.client.put(url, data={"code": "ti"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["invalidParams"][0]["code"], "invalid_choice")
        self.assertEqual(error["invalidParams"][0]["name"], "code")


class CustomizedCompiledTranslationsViewTests(APITestCase):
    def test_view_returns_compiled_file_json_data(self):
        translations_metadata = TranslationsMetaDataFactory.create(
            with_compiled_asset=True
        )
        file_content = json.load(translations_metadata.compiled_asset.file)

        endpoint = reverse("api:i18n:customized-translations", args=["en"])
        response = self.client.get(endpoint)

        self.assertEqual(response.json(), file_content)

    def test_view_when_language_unsupported(self):
        endpoint = reverse("api:i18n:customized-translations", args=["gr"])
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_with_not_compiled_asset(self):
        translations_metadata = TranslationsMetaDataFactory.create()

        # make sure no compiled asset is present
        self.assertEqual(translations_metadata.processing_status, StatusChoices.pending)
        self.assertIsNone(translations_metadata.last_updated)

        endpoint = reverse("api:i18n:customized-translations", args=["en"])
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)  # pyright: ignore [reportAttributeAccessIssue]
