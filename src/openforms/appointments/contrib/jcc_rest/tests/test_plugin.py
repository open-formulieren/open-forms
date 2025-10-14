from django.test import TestCase

from openforms.appointments.contrib.jcc_rest.plugin import JccRestPlugin

from ....base import Product


class PluginTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plugin = JccRestPlugin("jcc")

    def test_get_all_locations(self):
        locations = self.plugin.get_locations()

        self.assertEqual(len(locations), 3)
        # Check the first location
        location = locations[0]
        self.assertEqual(location.identifier, "f3b8864b-2e08-4d01-99db-e36f49f3e19c")
        self.assertEqual(location.name, "Gemeentehuis Meerbergen")
        self.assertEqual(location.address, "Raadhuisplein 1")
        self.assertEqual(location.postalcode, "1234 AZ")
        self.assertEqual(location.city, "Meerbergen")

    def test_get_locations(self):
        product = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c",
            name="Paspoort aanvraag",
        )

        locations = self.plugin.get_locations([product])

        self.assertEqual(len(locations), 1)
        # Check the location
        location = locations[0]
        self.assertEqual(location.identifier, "f3b8864b-2e08-4d01-99db-e36f49f3e19c")
        self.assertEqual(location.name, "Gemeentehuis Meerbergen")
        self.assertEqual(location.address, "Raadhuisplein 1")
        self.assertEqual(location.postalcode, "1234 AZ")
        self.assertEqual(location.city, "Meerbergen")
