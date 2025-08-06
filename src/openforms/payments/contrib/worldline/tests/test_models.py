from django.test import TestCase

from .factories import WorldlineMerchantFactory


class WorldlineMerchantTests(TestCase):
    def test_string_representation(self):
        merchant = WorldlineMerchantFactory(label="Maykin Media")

        self.assertEqual(str(merchant), "Maykin Media")
