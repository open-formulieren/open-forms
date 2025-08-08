from django.test import TestCase

from .factories import WorldlineMerchantFactory, WorldlineWebhookConfigurationFactory


class WorldlineMerchantTests(TestCase):
    def test_string_representation(self):
        merchant = WorldlineMerchantFactory(label="Maykin Media")

        self.assertEqual(str(merchant), "Maykin Media")


class WorldlineWebhookConfigurationTests(TestCase):
    def test_string_representation(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory()

        self.assertEqual(
            str(webhook_configuration), webhook_configuration.webhook_key_id
        )
