import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase

from freezegun import freeze_time
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.utils.date import get_today
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ....base import Location, Product
from ..client import Location as RawLocation
from ..exceptions import JccRestException
from ..models import JccRestConfig
from ..plugin import JccRestPlugin


def _scrub_access_token(response):
    if b"access_token" in response["body"]["string"]:
        # An access token must be present in the response to ensure it passes oauthlib
        # validation
        response["body"]["string"] = b'{"access_token": "fake_access_token"}'
    return response


class PluginTests(OFVCRMixin, TestCase):
    """
    Test the JCC Rest API appointments plugin

    Note when re-recording the VCR cassettes:
     - At the point of writing this test, it's not clear how consistent the test data
       will be in the future, so changes to the tests might be needed.
     - Make sure to update the ``RECORDING_DATATIME`` class property to the date of
       recording.
    """

    RECORDING_DATETIME = "2026-01-09T12:34:56+02:00"

    def setUp(self):
        super().setUp()

        # The token requests are cached, so have to make sure cache is emptied to enable
        # testing the individual (and reverse) methods
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = JccRestPlugin("jcc")

        config = JccRestConfig.get_solo()
        config.service = ServiceFactory.create(
            api_root="https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/",
            auth_type=AuthTypes.oauth2_client_credentials,
            client_id=os.environ.get("JCC_REST_CLIENT_ID", "client_id"),
            secret=os.environ.get("JCC_REST_SECRET", "secret"),
            oauth2_token_url="https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/connect/token",
            oauth2_scope="warp-api",
        )
        config.save()

    def _get_vcr_kwargs(self, **kwargs) -> dict:
        kwargs = super()._get_vcr_kwargs(**kwargs)
        kwargs.setdefault("filter_headers", [])
        kwargs["filter_headers"].append("Authorization")
        kwargs["before_record_response"] = _scrub_access_token
        return kwargs

    def test_get_available_products_all(self):
        products = self.plugin.get_available_products()

        self.assertEqual(len(products), 26)
        # Select product with a description
        product = products[-2]
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
        self.assertEqual(product.amount, 1)
        self.assertEqual(product.description, "")

    def test_get_available_products_with_current_product(self):
        product = Product(
            identifier="637474a7-ea52-43f8-9e8a-30f3e0c13cf4",
            name="Partnerschap met toespraak - eigen BABS",
        )
        products = self.plugin.get_available_products(current_products=[product])

        # This product can only be combined with the received products. Ensure that they
        # do not include the current product.
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

    def test_get_locations_for_product(self):
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

        # Note: other users of the test environment can make appointments, so the
        # available dates might not be consistent, so just ensure that is not an empty
        # list. This is also not impossible of course, but less likely.
        self.assertTrue(len(dates) != 0)

    @freeze_time(RECORDING_DATETIME)
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
        # product and location, so just ensure the dates are within the specified range
        self.assertTrue(len(dates) != 0)
        self.assertTrue(min(dates) >= start_at)
        self.assertTrue(max(dates) <= end_at)

    @freeze_time(RECORDING_DATETIME)
    def test_get_times(self):
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

        today = get_today()
        times = self.plugin.get_times(products=[product], location=location, day=today)

        # Exact times might change, depending on the created appointments for this
        # product and location, so just ensure all datetimes are from today
        self.assertTrue(len(times) != 0)
        self.assertTrue(min(times).date() == today)
        self.assertTrue(max(times).date() == today)

    def test_handles_errors_gracefully(self):
        """
        Ensure that errors are handled gracefully (not passing a product when getting
        available dates returns a 400).
        """
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
            products=[], location=location, start_at=start_at, end_at=end_at
        )

        self.assertTrue(len(dates) == 0)

    def test_create_location(self):
        """
        Ensure address processing functions as expected. Note that ideally we would like
        to test this using the endpoint, but we have no control over the available
        locations on the test environment.
        """
        raw_location: RawLocation = {
            "id": "id",
            "auditId": "auditId",
            "address": {
                "id": "id",
                "auditId": "auditId",
                "country": {
                    "id": "c59f75c0-1106-4423-b7d2-5d2b7c41c7bc",
                    "isoCode": "NL",
                    "name": "Nederland",
                },
                "streetName": "",
                "houseNumber": "",
                "houseNumberSuffix": "",
            },
            "isDefault": True,
        }

        with self.subTest("No information"):
            location = self.plugin._create_location(raw_location)  # pyright: ignore[reportAttributeAccessIssue]
            self.assertEqual(location.address, "")

        with self.subTest("Street name"):
            raw_location["address"]["streetName"] = "Street"
            location = self.plugin._create_location(raw_location)  # pyright: ignore[reportAttributeAccessIssue]
            self.assertEqual(location.address, "Street")

        with self.subTest("Street name and house number"):
            raw_location["address"]["houseNumber"] = "10"
            location = self.plugin._create_location(raw_location)  # pyright: ignore[reportAttributeAccessIssue]
            self.assertEqual(location.address, "Street 10")

        with self.subTest("Street name, house number and suffix"):
            raw_location["address"]["houseNumberSuffix"] = "b"
            location = self.plugin._create_location(raw_location)  # pyright: ignore[reportAttributeAccessIssue]
            self.assertEqual(location.address, "Street 10b")

    def test_config_check_ok(self):
        try:
            self.plugin.check_config()
        except InvalidPluginConfiguration:
            self.failureException("Config check should have passed.")


class FailedConfigCheckTests(TestCase):
    def test_check_config_no_service_configured(self):
        plugin = JccRestPlugin("jcc")

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @patch("openforms.appointments.contrib.jcc_rest.plugin.JccRestClient")
    def test_check_config_endpoint_does_not_respond(self, mock_client):
        class Client:
            def __enter__(self):
                pass

            def __exit__(self, *args, **kwargs):
                pass

            def get_version(self):
                raise JccRestException

        mock_client.return_value = Client()

        plugin = JccRestPlugin("jcc")

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()
