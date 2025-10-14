from django.test import TestCase

from openforms.appointments.contrib.jcc_rest.plugin import JccRestPlugin

from ....base import Product, Location


# TODO-5696: move the Product and Location constants to setUpClass method. Will be
#  easier to update if JCC decides to change them
class PluginTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plugin = JccRestPlugin("jcc")

    def test_get_available_products_all(self):
        products = self.plugin.get_available_products()

        self.assertEqual(len(products), 28)
        # Check the first product
        product = products[0]
        self.assertEqual(product.identifier, "cbdba351-a743-4664-8347-20d17134ad5d")
        self.assertEqual(product.name, "Horecavergunning (aanvraag)")
        self.assertEqual(product.code, "")
        self.assertEqual(product.amount, 1)
        self.assertEqual(product.description, None)

        # Check product with description
        product = products[26]
        self.assertEqual(product.identifier, "e4dc7942-d394-4c39-a153-bdabc62634f8")
        self.assertEqual(product.name, "Identiteitskaart (aanvraag)")
        self.assertTrue(product.description.startswith("<P>Wat heeft u nodig?"))

    def test_get_available_products_with_location(self):
        products = self.plugin.get_available_products(
            location_id="f9332b85-2ca3-4b42-aaa9-07e37c010a83"
        )

        self.assertEqual(len(products), 8)
        # Check the first product
        product = products[0]
        self.assertEqual(product.identifier, "637474a7-ea52-43f8-9e8a-30f3e0c13cf4")
        self.assertEqual(product.name, "Partnerschap met toespraak - eigen BABS")
        self.assertEqual(product.code, "")
        self.assertEqual(product.amount, 1)
        self.assertEqual(product.description, None)

    def test_get_available_products_with_current_product(self):
        product = Product(
            identifier="637474a7-ea52-43f8-9e8a-30f3e0c13cf4",
            name="Partnerschap met toespraak - eigen BABS",
        )
        products = self.plugin.get_available_products(current_products=[product])

        # This product can only be combined with the received products. Ensure that they
        # do not include the current product
        self.assertEqual(len(products), 3)
        for received_product in products:
            self.assertNotEqual(received_product.identifier, product.identifier)

    def test_get_available_products_with_location_and_current_product(self):
        product = Product(
            identifier="637474a7-ea52-43f8-9e8a-30f3e0c13cf4",
            name="Partnerschap met toespraak - eigen BABS",
        )
        products = self.plugin.get_available_products(
            current_products=[product],
            location_id="f9332b85-2ca3-4b42-aaa9-07e37c010a83",
        )

        # At this specific location, this product can only be combined with one other
        # product. Ensure it is not the already selected product.
        self.assertEqual(len(products), 1)
        self.assertNotEqual(products[0].identifier, product.identifier)

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

    def test_get_dates(self):
        product = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c",
            name="Paspoort aanvraag",
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c",
            name="Gemeentehuis Meerbergen",
            address="Raadhuisplein 1",
            postalcode="1234 AZ",
            city="Meerbergen",
        )

        dates = self.plugin.get_dates(products=[product], location=location)

        # TODO-5696: what to assert here? The number of dates can change over time,
        #  depending on the created appointments. Perhaps just ensure that the number of
        #  available dates is not zero? I guess it could happen in theory, but it's
        #  unlikely I would say
        self.assertTrue(len(dates) != 0)

    def test_get_dates_with_custom_range(self):
        product = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c",
            name="Paspoort aanvraag",
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c",
            name="Gemeentehuis Meerbergen",
            address="Raadhuisplein 1",
            postalcode="1234 AZ",
            city="Meerbergen",
        )

        start_at = get_today()
        end_at = start_at + timedelta(days=7)
        dates = self.plugin.get_dates(
            products=[product], location=location, start_at=start_at, end_at=end_at
        )

        # Exact dates might change, depending on the created appointments for this
        # activity and location, so just ensure the dates are within the specified range
        self.assertTrue(min(dates) >= start_at)
        self.assertTrue(max(dates) <= end_at)
