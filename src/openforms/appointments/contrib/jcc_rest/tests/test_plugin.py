import os
from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.utils.date import TIMEZONE_AMS, get_today
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ....base import AppointmentDetails, CustomerDetails, Location, Product
from ....exceptions import AppointmentCreateFailed, AppointmentDeleteFailed
from ..client import Location as RawLocation
from ..constants import CustomerFields
from ..exceptions import GracefulJccRestException, JccRestException
from ..models import JccRestConfig
from ..plugin import JccRestPlugin


def _scrub_access_token(response):
    if b"access_token" in response["body"]["string"]:
        # An access token must be present in the response to ensure it passes oauthlib
        # validation
        response["body"]["string"] = b'{"access_token": "fake_access_token"}'
    return response


@override_settings(LANGUAGE_CODE="en")
class PluginTests(OFVCRMixin, TestCase):
    """
    Test the JCC Rest API appointments plugin

    Instead of mocking responses, we do real requests to a JCC test environment *once*
    and record the responses with VCR.

    When JCC update their service, responses on VCR cassettes might be stale, and
    we'll need to re-test against the real service to assert everything still works.

    To do so:

    #. Define the required environmental variables and their values (`JCC_REST_CLIENT_ID`,`JCC_REST_SECRET`)
    #. Ensure the config is still valid:
       - `token` needs to be valid
       - endpoints must work as expected
       - data is still valid
    #. Delete the VCR cassettes
    #. Update the ``RECORDING_DATATIME`` class attribute to the date of recording.
    #. Run the tests
    #. Inspect the diff of the new cassettes
    #. Make sure sensitive information related to tokens or credentials are not present
    #  in the cassettes.

    The default dev settings set the record mode to 'once', but if you need a different
    one, see the :module:`openforms.utils.tests.vcr` documentation.

    Note when re-recording the VCR cassettes:
     - At the point of writing these tests, it's not clear how consistent the test data
       will be in the future, so changes to the tests might be needed.
    """

    RECORDING_DATETIME: str = "2026-02-02T12:32:56+02:00"

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
        assert "filter_headers" in kwargs
        assert "Authorization" in kwargs["filter_headers"]
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
        # Check the first location to ensure all location information is set correctly.
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

        # We don't really care about which exact location is related to this product, so
        # just ensure we receive a location. Note that this list length is different
        # from when we request all locations.
        self.assertEqual(len(locations), 1)

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

        # Note: other users of the test environment can make appointments, which means
        # the available dates might not be consistent, so just ensure that is not an
        # empty list. This is also not impossible of course, but less likely.
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
        Ensure that errors are handled gracefully (requesting a date range in the past
        returns a 500 error).
        """
        product = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c",
            name="Paspoort aanvraag",
        )
        location = Location(
            identifier="fake_location",
            name="Foo",
        )

        start_at = date(2025, 12, 31)
        end_at = start_at + timedelta(days=7)
        dates = self.plugin.get_dates(
            products=[product], location=location, start_at=start_at, end_at=end_at
        )

        self.assertTrue(len(dates) == 0)

    @patch("openforms.appointments.contrib.jcc_rest.client.Client.get_location_list")
    def test_address_processing(self, m):
        """
        Ensure address processing functions as expected. Note that ideally we would like
        to test this using the endpoint, but this data is not available
        """
        raw_location: RawLocation = {
            "id": "id",
            "locationNumber": 2,
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
        m.return_value = [raw_location]

        with self.subTest("No information"):
            locations = self.plugin.get_locations()
            self.assertEqual(locations[0].address, "")

        with self.subTest("Street name"):
            raw_location["address"]["streetName"] = "Street"
            locations = self.plugin.get_locations()
            self.assertEqual(locations[0].address, "Street")

        with self.subTest("Street name and house number"):
            raw_location["address"]["houseNumber"] = "10"
            locations = self.plugin.get_locations()
            self.assertEqual(locations[0].address, "Street 10")

        with self.subTest("Street name, house number and suffix"):
            raw_location["address"]["houseNumberSuffix"] = "b"
            locations = self.plugin.get_locations()
            self.assertEqual(locations[0].address, "Street 10b")

    def test_config_check_ok(self):
        try:
            self.plugin.check_config()
        except InvalidPluginConfiguration:
            self.failureException("Config check should have passed.")

    def test_required_customer_fields_with_existing_products(self):
        """
        The specific activity is covering all the possible states of a field (visible,
        hidden and required).
        """
        product1 = Product(
            identifier="c956d136-57a0-4c53-9673-378f41044631",
            name="Schuldhulpverlening",
        )
        product2 = Product(
            identifier="53410a47-6ede-4225-81e0-4ebffaae0ef3",
            name="Geboorteaangifte",
        )

        required_fields = self.plugin.get_required_customer_fields([product1, product2])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "radio",
                        "key": "gender",
                        "label": "Gender",
                        "validate": {"required": False},
                        "values": [
                            {"value": 1, "label": "Male"},
                            {"value": 2, "label": "Female"},
                            {"value": 0, "label": "Other"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "firstName",
                        "label": "First name",
                        "autocomplete": "first-name",
                        "validate": {"maxLength": 128, "required": False},
                    },
                    {
                        "type": "textfield",
                        "key": "lastNamePrefix",
                        "label": "Last name prefix",
                        "autocomplete": "family-name-prefix",
                        "validate": {"maxLength": 128, "required": False},
                    },
                    {
                        "type": "date",
                        "key": "birthDate",
                        "label": "Date of birth",
                        "autocomplete": "date-of-birth",
                        "validate": {"required": False},
                        "openForms": {"widget": "inputGroup"},
                    },
                    {
                        "type": "email",
                        "key": "emailAddress",
                        "label": "Email address",
                        "autocomplete": "email-address",
                        "validate": {"maxLength": 254, "required": False},
                    },
                    {
                        "type": "textfield",
                        "key": "socialSecurityNumber",
                        "label": "Social security number",
                        "autocomplete": "social-security-number",
                        "validate": {"maxLength": 16, "required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_areFirstNameOrInitialsRequired_and_both_fields_visible(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both firstName and initials to be visible and
        # areFirstNameOrInitialsRequired to be True)

        m.return_value = {
            "areFirstNameOrInitialsRequired": True,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "mainPhoneNumber": 1,
            "mobilePhoneNumber": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "textfield",
                        "key": "firstName",
                        "label": "First name",
                        "autocomplete": "first-name",
                        "validate": {"maxLength": 128, "required": False},
                        "description": "At least one of the following fields must be filled in: First name, Initials",
                    },
                    {
                        "type": "textfield",
                        "key": "initials",
                        "label": "Initials",
                        "autocomplete": "initials",
                        "validate": {"maxLength": 128, "required": False},
                        "description": "At least one of the following fields must be filled in: First name, Initials",
                    },
                ],
                [
                    {
                        "type": "require_one_of",
                        "fields": ("firstName", "initials"),
                        "error_message": "At least one of the following fields is required: First name, Initials.",
                    }
                ],
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_areFirstNameOrInitialsRequired_and_both_fields_hidden(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both firstName and initials to be hidden and
        # areFirstNameOrInitialsRequired to be True)

        m.return_value = {
            "areFirstNameOrInitialsRequired": True,
            "firstName": 1,
            "initials": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "mainPhoneNumber": 1,
            "mobilePhoneNumber": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "firstName",
                        "label": "First name",
                        "autocomplete": "first-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_areFirstNameOrInitialsRequired_and_both_fields_required(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both firstName and initials to be required and
        # areFirstNameOrInitialsRequired to be True)

        m.return_value = {
            "areFirstNameOrInitialsRequired": True,
            "firstName": 2,
            "initials": 2,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "mainPhoneNumber": 1,
            "mobilePhoneNumber": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "textfield",
                        "key": "firstName",
                        "label": "First name",
                        "autocomplete": "first-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "textfield",
                        "key": "initials",
                        "label": "Initials",
                        "autocomplete": "initials",
                        "validate": {"maxLength": 128, "required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_areFirstNameOrInitialsRequired_and_one_field_missing(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both firstName and initials to be required and
        # areFirstNameOrInitialsRequired to be True)

        m.return_value = {
            "areFirstNameOrInitialsRequired": True,
            "firstName": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "mainPhoneNumber": 1,
            "mobilePhoneNumber": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "textfield",
                        "key": "initials",
                        "label": "Initials",
                        "autocomplete": "initials",
                        "validate": {"maxLength": 128, "required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_isAnyPhoneNumberRequired_and_both_fields_visible(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both mobilePhoneNumber and mainPhoneNumber to be
        # visible and isAnyPhoneNumberRequired to be True)

        m.return_value = {
            "isAnyPhoneNumberRequired": True,
            "firstName": 1,
            "initials": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }
        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "phoneNumber",
                        "key": "mobilePhoneNumber",
                        "label": "Mobile phone number",
                        "autocomplete": "mobile-phone-number",
                        "validate": {"maxLength": 16, "required": False},
                        "description": "At least one of the following fields must be filled in: Phone number, Mobile phone number",
                    },
                    {
                        "type": "phoneNumber",
                        "key": "phoneNumber",
                        "label": "Phone number",
                        "autocomplete": "phone-number",
                        "validate": {"required": False},
                        "description": "At least one of the following fields must be filled in: Phone number, Mobile phone number",
                    },
                ],
                [
                    {
                        "type": "require_one_of",
                        "fields": ("phoneNumber", "mobilePhoneNumber"),
                        "error_message": "At least one of the following fields is required: Phone number, Mobile phone number.",
                    }
                ],
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_isAnyPhoneNumberRequired_and_both_fields_required(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both mobilePhoneNumber and mainPhoneNumber to be
        # required and isAnyPhoneNumberRequired to be True)

        m.return_value = {
            "isAnyPhoneNumberRequired": True,
            "mainPhoneNumber": 2,
            "mobilePhoneNumber": 2,
            "firstName": 1,
            "initials": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "phoneNumber",
                        "key": "mobilePhoneNumber",
                        "label": "Mobile phone number",
                        "autocomplete": "mobile-phone-number",
                        "validate": {"maxLength": 16, "required": True},
                    },
                    {
                        "type": "phoneNumber",
                        "key": "phoneNumber",
                        "label": "Phone number",
                        "autocomplete": "phone-number",
                        "validate": {"required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_isAnyPhoneNumberRequired_and_both_fields_hidden(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both mobilePhoneNumber and mainPhoneNumber to be
        # hidden and isAnyPhoneNumberRequired to be True)

        m.return_value = {
            "isAnyPhoneNumberRequired": True,
            "mainPhoneNumber": 1,
            "mobilePhoneNumber": 1,
            "firstName": 1,
            "initials": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "phoneNumber",
                        "key": "phoneNumber",
                        "label": "Phone number",
                        "autocomplete": "phone-number",
                        "validate": {"required": True},
                    },
                ],
                None,
            ),
        )

    @patch(
        "openforms.appointments.contrib.jcc_rest.client.Client.get_required_customer_fields"
    )
    def test_required_customer_fields_with_isAnyPhoneNumberRequired_and_one_field_is_missing(
        self, m
    ):
        # TODO
        # Check if such an example has been added to the JCC test instance and replace
        # the mocked response (we need both mobilePhoneNumber and mainPhoneNumber to be
        # hidden and isAnyPhoneNumberRequired to be True)

        m.return_value = {
            "isAnyPhoneNumberRequired": True,
            "mainPhoneNumber": 1,
            "firstName": 1,
            "initials": 1,
            "gender": 1,
            "lastNamePrefix": 1,
            "birthDate": 1,
            "socialSecurityNumber": 1,
            "nationality": 1,
            "language": 1,
            "emailAddress": 1,
            "streetName": 1,
            "houseNumber": 1,
            "houseNumberSuffix": 1,
            "postalCode": 1,
            "city": 1,
            "country": 1,
        }

        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        self.assertEqual(
            required_fields,
            (
                [
                    {
                        "type": "textfield",
                        "key": "lastName",
                        "label": "Last name",
                        "autocomplete": "family-name",
                        "validate": {"maxLength": 128, "required": True},
                    },
                    {
                        "type": "phoneNumber",
                        "key": "mobilePhoneNumber",
                        "label": "Mobile phone number",
                        "autocomplete": "mobile-phone-number",
                        "validate": {"maxLength": 16, "required": True},
                    },
                ],
                None,
            ),
        )

    @freeze_time(RECORDING_DATETIME)
    def test_create_retrieve_and_cancel_appointment_flow(self):
        product = Product(
            identifier="2e656741-db4d-4c75-ae57-97fda6ce5ce8",
            name="Omgevingsvergunning (aanvraag)",
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c", name="test1"
        )
        customer = CustomerDetails(
            details={
                CustomerFields.first_name: "Vat",
                CustomerFields.last_name: "Boei",
                CustomerFields.date_of_birth: "2000-02-02",
                CustomerFields.gender: 0,
            }
        )

        # 1. fetch the available dates
        available_dates = self.plugin.get_dates(
            products=[product], location=location, start_at=get_today()
        )
        assert available_dates != []

        # 2. fetch the available times
        available_times = self.plugin.get_times(
            products=[product], location=location, day=available_dates[0]
        )
        assert available_times != []

        # 3. create the appointment
        appointment_id = self.plugin.create_appointment(
            products=[product],
            location=location,
            start_at=available_times[0],
            client=customer,
        )

        self.assertIsInstance(appointment_id, str)

        # 4. fetch the appointment's details
        appointment_details = self.plugin.get_appointment_details(appointment_id)

        self.assertEqual(type(appointment_details), AppointmentDetails)

        self.assertEqual(len(appointment_details.products), 1)
        self.assertEqual(appointment_details.identifier, appointment_id)
        self.assertEqual(
            appointment_details.products[0].identifier,
            "2e656741-db4d-4c75-ae57-97fda6ce5ce8",
        )
        self.assertEqual(
            appointment_details.products[0].name, "Omgevingsvergunning (aanvraag)"
        )
        self.assertEqual(appointment_details.products[0].amount, 1)

        self.assertEqual(
            appointment_details.location.identifier,
            "f3b8864b-2e08-4d01-99db-e36f49f3e19c",
        )
        self.assertEqual(appointment_details.location.name, "Gemeentehuis Meerbergen")
        self.assertEqual(appointment_details.location.address, "Raadhuisplein 1")
        self.assertEqual(appointment_details.location.postalcode, "1234 AZ")
        self.assertEqual(appointment_details.location.city, "Meerbergen")

        self.assertEqual(
            appointment_details.start_at, available_times[0].replace(tzinfo=None)
        )
        self.assertIsNotNone(appointment_details.end_at)
        self.assertEqual(appointment_details.remarks, None)
        self.assertIsNotNone(appointment_details.other)

        # 5. cancel the appointment
        self.plugin.delete_appointment(appointment_id)

    @freeze_time(RECORDING_DATETIME)
    def test_create_appointment_with_multiple_products(self):
        product1 = Product(
            identifier="637474a7-ea52-43f8-9e8a-30f3e0c13cf4",
            name="Partnerschap met toespraak - eigen BABS",
        )
        product2 = Product(
            identifier="27535042-9f33-498f-b559-39137639bad3",
            name="Huwelijk met toespraak - BABS3",
        )
        location = Location(identifier="f9332b85-2ca3-4b42-aaa9-07e37c010a83", name="")
        customer = CustomerDetails(
            details={
                CustomerFields.last_name: "Boei",
                CustomerFields.email_address: "testBoei@example.com",
                CustomerFields.phone_number: "0612345678",
                CustomerFields.gender: 0,
            }
        )

        # 1. fetch the available dates
        available_dates = self.plugin.get_dates(
            products=[product1, product2], location=location, start_at=get_today()
        )
        assert available_dates != []

        # 2. fetch the available times
        available_times = self.plugin.get_times(
            products=[product1, product2], location=location, day=available_dates[0]
        )
        assert available_times != []

        # 3. create the appointment
        appointment_id = self.plugin.create_appointment(
            products=[product1, product2],
            location=location,
            start_at=available_times[0],
            client=customer,
        )

        self.assertTrue(isinstance(appointment_id, str))

    @freeze_time(RECORDING_DATETIME)
    def test_appointment_with_multiple_persons(self):
        product = Product(
            identifier="2e656741-db4d-4c75-ae57-97fda6ce5ce8",
            name="Omgevingsvergunning (aanvraag)",
            amount=2,
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c",
            name="Gemeentehuis Meerbergen",
        )
        customer = CustomerDetails(
            details={
                CustomerFields.first_name: "Vat",
                CustomerFields.last_name: "Boei",
                CustomerFields.date_of_birth: "2000-02-02",
                CustomerFields.gender: 0,
            }
        )

        # 1. fetch the available dates
        available_dates = self.plugin.get_dates(
            products=[product], location=location, start_at=get_today()
        )
        assert available_dates != []

        # 2. fetch the available times
        available_times = self.plugin.get_times(
            products=[product], location=location, day=available_dates[0]
        )
        assert available_times != []

        # 3. create the appointment
        appointment_id = self.plugin.create_appointment(
            products=[product],
            location=location,
            start_at=available_times[0],
            client=customer,
        )

        self.assertTrue(isinstance(appointment_id, str))

    def test_create_appointment_fails_with_missing_body_data(self):
        """Missing the products"""
        product = Product(
            identifier="",
            name="",
            amount=1,
        )
        customer = CustomerDetails(
            details={
                CustomerFields.last_name: "Boei",
                CustomerFields.date_of_birth: "2000-02-02",
            }
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c", name="test1"
        )
        start_at = timezone.make_aware(
            datetime(2025, 10, 21, 8, 0, 0), timezone=TIMEZONE_AMS
        )

        with self.assertRaises(GracefulJccRestException):
            self.plugin.create_appointment(
                products=[product],
                location=location,
                start_at=start_at,
                client=customer,
            )

    @patch("openforms.appointments.contrib.jcc_rest.client.Client.add_appointment")
    def test_create_appointment_with_error_returned(self, m):
        # simulate an unexpected return value in the appointment create (with a 200 response)
        m.return_value = {"id": "an-id", "code": "33333", "acknowledgeIsSuccess": False}

        product = Product(
            identifier="2e656741-db4d-4c75-ae57-97fda6ce5ce8",
            name="Omgevingsvergunning (aanvraag)",
        )
        location = Location(
            identifier="f3b8864b-2e08-4d01-99db-e36f49f3e19c", name="test1"
        )
        customer = CustomerDetails(
            details={
                CustomerFields.first_name: "Vat",
                CustomerFields.last_name: "Boei",
                CustomerFields.date_of_birth: "2000-02-02",
                CustomerFields.gender: 0,
            }
        )

        # 3. create the appointment
        with self.assertRaises(AppointmentCreateFailed):
            self.plugin.create_appointment(
                products=[product],
                location=location,
                start_at=datetime.fromisoformat("2026-01-16T09:30:00"),
                client=customer,
            )

    @patch("openforms.appointments.contrib.jcc_rest.client.Client.cancel_appointment")
    def test_delete_appointment_with_error_returned(self, m):
        # simulate an unexpected return value in the appointment delete (with a 200 response)
        m.return_value = {"code": "222222"}

        with self.assertRaises(AppointmentDeleteFailed):
            self.plugin.delete_appointment("invalid-id")


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
