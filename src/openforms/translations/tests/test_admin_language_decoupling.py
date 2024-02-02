from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory


@disable_admin_mfa()
class AdminLanguageTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

    def test_language_cookie_ignored_by_admin(self):
        # sets the language cookie
        _response = self.app.put_json(reverse("api:i18n:language"), {"code": "en"})
        assert _response.headers["Content-Language"] == "en"
        assert self.app.cookies["openforms_language"] == "en"

        admin_index = self.app.get(
            reverse("admin:index"),
            headers={"Accept-Language": "nl-NL, nl;q=0.9, en;q=0.5"},
            user=self.user,
        )

        self.assertEqual(admin_index["Content-Language"], "nl")

    def test_user_preference_overrides_browser_prefs(self):
        self.user.ui_language = "en"
        self.user.save()

        admin_index = self.app.get(
            reverse("admin:index"),
            headers={"Accept-Language": "nl-NL, nl;q=0.9, en;q=0.5"},
            user=self.user,
        )

        self.assertEqual(admin_index["Content-Language"], "en")
