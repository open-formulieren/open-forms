from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.test import APITestCase


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
