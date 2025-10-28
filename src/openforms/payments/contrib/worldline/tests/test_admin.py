from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.payments.registry import register

from .factories import WorldlineMerchantFactory, WorldlineWebhookConfigurationFactory


@disable_admin_mfa()
@override_settings(BASE_URL="https://example.com/foo")
class WorldlineMerchantAdminTest(WebTest):
    def test_merchant_list_page(self):
        user = SuperUserFactory.create()
        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(None)
        url = reverse("admin:payments_worldline_worldlinemerchant_changelist")

        with self.subTest("Overview without entries"):
            response = self.app.get(url, user=user)

            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, webhook_url)

        with self.subTest("Overview with entries"):
            WorldlineMerchantFactory.create()

            response = self.app.get(url, user=user)

            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, webhook_url)


@disable_admin_mfa()
class WorldlineWebhookConfigurationAdminTest(WebTest):
    @override_settings(BASE_URL="https://example.com/foo")
    def test_webhook_configuration_detail_page(self):
        user = SuperUserFactory.create()
        config = WorldlineWebhookConfigurationFactory.create()
        url = reverse(
            "admin:payments_worldline_worldlinewebhookconfiguration_change",
            args=(config.pk,),
        )
        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(None)

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, webhook_url)
