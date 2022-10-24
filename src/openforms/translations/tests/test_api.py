from collections import namedtuple

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from hypothesis import given, settings, strategies as st

# from hypothesis.extra.django import TestCase
from rest_framework.test import APISimpleTestCase

Language = namedtuple("Language", "conf local")


class I18NAPITests(APISimpleTestCase):
    databases = ["default"]

    @given(
        st.lists(
            st.sampled_from(
                [
                    Language(("en", _("English")), "English"),
                    Language(("nl", _("Dutch")), "Nederlands"),
                    Language(("tr", _("Turkish")), "Türkçe"),
                ]
            ),
            unique=True,
        )
    )
    @settings(deadline=500)
    def test_info_contains_available_langauges(self, languages):
        with override_settings(
            USE_I18N=True,
            LANGUAGES=[lang.conf for lang in languages],
        ):
            # expect language names in their local representation
            expected = [
                {"code": lang.conf[0], "name": lang.local} for lang in languages
            ]
            url = reverse("api:i18n:info")
            response = self.client.get(url)
            available = response.json()["langauges"]
            self.assertEqual(available, expected)

    @override_settings(
        USE_I18N=True,
        LANGUAGE_CODE="en",
        LANGUAGES=[
            ("en", _("English")),
            ("nl", _("Dutch")),
        ],
    )
    def test_info_contains_active_language(self):
        # default fallback
        url = reverse("api:i18n:info")
        response = self.client.get(url)
        current = response.json()["current"]
        self.assertEqual(current, "en")

    @override_settings(
        USE_I18N=True,
        LANGUAGE_CODE="en",
        LANGUAGES=[
            ("en", _("English")),
            ("nl", _("Dutch")),
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.locale.LocaleMiddleware",
            "django.middleware.common.CommonMiddleware",
        ],
    )
    def test_info_negotiates_active_language_from_header(self):
        url = reverse("api:i18n:info")
        response = self.client.get(
            url, HTTP_ACCEPT_LANGUAGE="nl-BE, nl;q=0.9, en;q=0.8"
        )
        current = response.json()["current"]
        self.assertEqual(current, "nl")

    @override_settings(
        USE_I18N=True,
        LANGUAGE_CODE="en",
        LANGUAGES=[
            ("en", _("English")),
            ("nl", _("Dutch")),
        ],
        LANGUAGE_COOKIE_NAME="openforms-language",
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.locale.LocaleMiddleware",
            "django.middleware.common.CommonMiddleware",
        ],
    )
    def test_put_overrides_negotiated_current(self):
        SELECT = "en"
        url = reverse("api:i18n:language")
        response = self.client.put(
            url,
            data={"code": SELECT},
            HTTP_ACCEPT_LANGUAGE="nl-BE, nl;q=0.9, en;q=0.8",
        )
        self.assertEqual(response.status_code, 204)

        url = reverse("api:i18n:info")
        response = self.client.get(
            url,
            HTTP_ACCEPT_LANGUAGE="nl-BE, nl;q=0.9, en;q=0.8",
        )
        current = response.json()["current"]
        self.assertEqual(current, SELECT)

    @override_settings(
        USE_I18N=True,
        LANGUAGE_CODE="en",
        LANGUAGES=[
            ("en", _("English")),
            ("nl", _("Dutch")),
        ],
        LANGUAGE_COOKIE_NAME="openforms-language",
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.locale.LocaleMiddleware",
            "django.middleware.common.CommonMiddleware",
        ],
    )
    def test_put_language_checks_for_availability(self):
        url = reverse("api:i18n:language")
        # ትግርኛ is not available
        response = self.client.put(url, data={"code": "ti"})
        self.assertEqual(response.status_code, 400)
