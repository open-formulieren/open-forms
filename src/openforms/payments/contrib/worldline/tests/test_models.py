from django.test import TestCase

from .factories import WorldlineMerchantFactory, WorldlineWebhookEntryFactory


class WorldlineMerchantTests(TestCase):
    def test_string_representation(self):
        merchant = WorldlineMerchantFactory(label="Maykin Media")

        self.assertEqual(str(merchant), "Maykin Media")


class WorldlineWebhookEntryTests(TestCase):
    def test_string_representation(self):
        webhook_entry = WorldlineWebhookEntryFactory()

        self.assertEqual(str(webhook_entry), webhook_entry.webhook_key_id)
