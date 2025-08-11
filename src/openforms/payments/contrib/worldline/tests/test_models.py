from django.test import SimpleTestCase

from .factories import WorldlineMerchantFactory, WorldlineWebhookConfigurationFactory


class WorldlineMerchantTests(SimpleTestCase):
    def test_string_representation(self):
        merchant = WorldlineMerchantFactory.build(label="Maykin Media")

        self.assertEqual(str(merchant), "Maykin Media")


class WorldlineWebhookConfigurationTests(SimpleTestCase):
    def test_string_representation(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.build()

        self.assertEqual(
            str(webhook_configuration), webhook_configuration.webhook_key_id
        )
