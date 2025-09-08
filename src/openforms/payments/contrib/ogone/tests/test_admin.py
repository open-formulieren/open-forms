from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from furl import furl
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.urls import reverse_plus


@disable_admin_mfa()
class OgoneMerchantAdminTest(WebTest):
    @override_settings(BASE_URL="https://example.com/foo")
    def test_add_ogone_merchant(self):
        user = SuperUserFactory.create()
        url = reverse("admin:payments_ogone_ogonemerchant_add")

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)

        feedback_url = (
            response.html.findAll("div", class_="field-feedback_url")[0]
            .findAll("div", class_="readonly")[0]
            .text
        )

        parsed_url = furl(feedback_url)

        self.assertEqual(parsed_url.host, "example.com")


@disable_admin_mfa()
class OgoneWebhookConfigurationAdminTest(WebTest):
    @override_settings()
    def test_webhook_configuration_detail_page(self):
        user = SuperUserFactory.create()
        webhook_url = reverse_plus(
            "payments:webhook",
            kwargs={"plugin_id": "worldline"},
            request=None,
        )
        url = reverse("admin:payments_ogone_ogonewebhookconfiguration_change")

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, webhook_url)
