import os
from datetime import datetime
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.appointments.base import CustomerDetails
from openforms.utils.date import TIMEZONE_AMS, get_today
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ....base import AppointmentDetails, Location, Product
from ..constants import CustomerFields
from ..exceptions import GracefulJccRestException
from ..models import JccRestConfig
from ..plugin import JccRestPlugin

# TODO
# Add tests for the extra field (isAnyPhoneNumberRequired) in `get_required_customer_fields`,
# when this is possible. The current activities do not have such an example.

# TODO
# Regenerate the cassettes when we have updated the plugin code


def _scrub_access_token(response):
    if b"access_token" in response["body"]["string"]:
        # An access token must be present in the response to ensure it passes oauthlib
        # validation
        response["body"]["string"] = b'{"access_token": "fake_access_token"}'
    return response


class JccRestPluginTests(OFVCRMixin, TestCase):
    """Test using JCC RESTful API.

    Instead of mocking responses, we do real requests to a JCC test environment *once*
    and record the responses with VCR.

    When JCC updates their service, responses on VCR cassettes might be stale, and
    we'll need to re-test against the real service to assert everything still works.

    To do so:

    #. Define the required environmental variables and their values (`JCC_REST_CLIENT_ID`,`JCC_REST_SECRET`)
    #. Ensure the config is still valid:
       - `token` needs to be valid
       - endpoints must work as expected
       - data is still valid
    #. Delete the VCR cassettes
    #. Run the test
    #. Inspect the diff of the new cassettes
    #. Make sure sensitive information related to tokens or credentials are not present
    #  in the cassettes.

    The default dev settings set the record mode to 'once', but if you need a different
    one, see the :module:`openforms.utils.tests.vcr` documentation.

    Note when re-recording the VCR cassettes:
     - At the point of writing these tests, it's not clear how consistent the test data
       will be in the future, so changes to the tests might be needed.
     - Make sure to update the ``RECORDING_DATATIME`` class property to the date of
       recording.
    """

    RECORDING_DATETIME: str = "2025-11-04T08:32:56+02:00"

    def setUp(self):
        super().setUp()

        # The token requests are cached, so have to make sure cache is emptied to enable
        # testing the individual (and reverse) methods
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = JccRestPlugin("jcc_rest")

        config = JccRestConfig.get_solo()
        config.service = ServiceFactory.create(
            api_root="https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/",
            auth_type=AuthTypes.oauth2_client_credentials,
            client_id=os.environ.get("JCC_REST_CLIENT_ID"),
            secret=os.environ.get("JCC_REST_SECRET"),
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

    def test_required_customer_fields_with_existing_products(self):
        product1 = Product(
            identifier="80b60dd2-6274-4c11-8d6b-5cb646ffe0f8",
            name="Evenementenvergunning (aanvraag)",
        )
        product2 = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c",
            name="Paspoort (aanvraag)",
        )

        required_fields = self.plugin.get_required_customer_fields([product1, product2])

        self.assertEqual(
            required_fields,
            [
                {
                    "type": "textfield",
                    "key": "firstName",
                    "label": "Voornaam",
                    "autocomplete": "first-name",
                    "validate": {"required": True, "maxLength": 128},
                },
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Achternaam",
                    "autocomplete": "family-name",
                    "validate": {"required": True, "maxLength": 128},
                },
                {
                    "type": "date",
                    "key": "birthDate",
                    "label": "Geboortedatum",
                    "autocomplete": "date-of-birth",
                    "validate": {"required": True},
                    "openForms": {"widget": "inputGroup"},
                },
            ],
        )

    def test_required_customer_fields_with_invalid_products(self):
        product = Product(identifier=str(uuid4()), name="")

        required_fields = self.plugin.get_required_customer_fields([product])

        # only the last name is by default added to the required fields
        self.assertEqual(
            required_fields,
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Achternaam",
                    "autocomplete": "family-name",
                    "validate": {"required": True, "maxLength": 128},
                },
            ],
        )

    def test_required_customer_fields_with_areFirstNameOrInitialsRequired(self):
        product1 = Product(
            identifier="2d03b4bf-c56f-41fd-bce2-621f174c8df2",
            name="Bouwvergunning aanvraag",
        )

        required_fields = self.plugin.get_required_customer_fields([product1])

        # initials is hidden so we fall back to the first name field
        self.assertEqual(
            required_fields,
            [
                {
                    "type": "textfield",
                    "key": "firstName",
                    "label": "Voornaam",
                    "autocomplete": "first-name",
                    "validate": {"required": True, "maxLength": 128},
                },
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Achternaam",
                    "autocomplete": "family-name",
                    "validate": {"required": True, "maxLength": 128},
                },
                {
                    "type": "date",
                    "key": "birthDate",
                    "label": "Geboortedatum",
                    "autocomplete": "date-of-birth",
                    "validate": {"required": True},
                    "openForms": {"widget": "inputGroup"},
                },
            ],
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

        self.assertTrue(isinstance(appointment_id, str))

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
        self.assertEqual(appointment_details.remarks, "")
        self.assertIsNotNone(appointment_details.other)

        # 5. cancel the appointment
        result = self.plugin.delete_appointment(appointment_id)

        self.assertIsNone(result)

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
                products=[], location=location, start_at=start_at, client=customer
            )
