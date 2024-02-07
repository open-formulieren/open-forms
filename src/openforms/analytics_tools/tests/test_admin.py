from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory


@disable_admin_mfa()
class AnalyticsConfigAdminTests(WebTest):
    def test_urls_cannot_have_trailing_slashes(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse(
            "admin:analytics_tools_analyticstoolsconfiguration_change", args=(1,)
        )

        fields = ("matomo_url", "piwik_url", "piwik_pro_url")
        for field in fields:
            with self.subTest(field=field):
                change_page = self.app.get(admin_url, user=superuser)
                form = change_page.form
                form[field] = "https://example.com/"

                response = form.submit()

                self.assertEqual(response.status_code, 200)
                errors = response.context["adminform"].form.errors
                self.assertIn(field, errors)
                self.assertEqual(errors.as_data()[field][0].code, "no_trailing_slash")

    def test_urls_without_trailing_slash_ok(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse(
            "admin:analytics_tools_analyticstoolsconfiguration_change", args=(1,)
        )

        fields = ("matomo_url", "piwik_url", "piwik_pro_url")
        for field in fields:
            with self.subTest(field=field):
                change_page = self.app.get(admin_url, user=superuser)
                form = change_page.form
                form[field] = "https://example.com"

                response = form.submit()

                self.assertEqual(response.status_code, 302)
