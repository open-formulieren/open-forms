import os
from datetime import datetime
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone

from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.utils.date import TIMEZONE_AMS
from openforms.utils.tests.vcr import OFVCRMixin

from ....base import CustomerDetails, Location, Product
from ....exceptions import AppointmentCreateFailed
from ..constants import CustomerFields
from ..models import JccRestConfig
from ..plugin import JccRestPlugin

JCC_REST_CLIENT_ID = os.environ.get("JCC_REST_CLIENT_ID", "")
JCC_REST_SECRET = os.environ.get("JCC_REST_SECRET", "")
JCC_REST_BASE_URL = "https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/"
JCC_REST_TOKEN_URL = "https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/connect/token"
JCC_REST_SCOPE = "warp-api"


# TODO
# Add tests for the extra fields in `get_required_customer_fields` (isAnyPhoneNumberRequired,
# areFirstNameOrInitialsRequired) when this is possible. The current activities (28) are
# not connected to customer fields result with these in it. If these are not needed according
# to JCC, this can be removed.

# Regenerate the cassettes when we have updated the plugin code


class JccRestPluginTests(OFVCRMixin, TestCase):
    """Test using JCC RESTful API.

    Instead of mocking responses, we do real requests to a JCC test environment
    *once* and record the responses with VCR.

    When JCC updates their service, responses on VCR cassettes might be stale, and
    we'll need to re-test against the real service to assert everything still works.

    To do so:

    #. Define the required environmental variables and their values (`JCC_REST_CLIENT_ID`, `JCC_REST_SECRET`)
    #. Ensure the config is still valid:
       - `token` needs to be valid
       - endpoints must work as expected
       - data is still valid
    #. Delete the VCR cassettes
    #. Run the test
    #. Inspect the diff of the new cassettes

    The default dev settings set the record mode to 'once', but if you need a different
    one, see the :module:`openforms.utils.tests.vcr` documentation.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = JccRestPlugin("jcc_rest")

        config = JccRestConfig.get_solo()
        config.service = ServiceFactory.create(
            api_root=JCC_REST_BASE_URL,
            auth_type=AuthTypes.oauth2_client_credentials,
            client_id=JCC_REST_CLIENT_ID,
            secret=JCC_REST_SECRET,
            oauth2_token_url=JCC_REST_TOKEN_URL,
            oauth2_scope=JCC_REST_SCOPE,
        )
        config.save()

    def test_required_customer_fields_with_existing_products(self):
        product1 = Product(
            identifier="6063baab-b077-4eaf-8671-98394793724c", name=""
        )  # all fields are hidden
        product2 = Product(
            identifier="cbdba351-a743-4664-8347-20d17134ad5d", name=""
        )  # all fields are hidden except the date of birth

        required_fields = self.plugin.get_required_customer_fields([product1, product2])

        self.assertEqual(
            required_fields,
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Achternaam",
                    "autocomplete": "family-name",
                    "validate": {"required": True},
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

        self.assertEqual(
            required_fields,
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Achternaam",
                    "autocomplete": "family-name",
                    "validate": {"required": True},
                },
            ],
        )

    def test_create_appointment_results_in_str_id(self):
        product = Product(
            identifier="2e656741-db4d-4c75-ae57-97fda6ce5ce8", name=""
        )  # all fields are hidden except the date of birth
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

        appointment_id = self.plugin.create_appointment(
            products=[product], location=location, start_at=start_at, client=customer
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

        with self.assertRaises(AppointmentCreateFailed):
            self.plugin.create_appointment(
                products=[], location=location, start_at=start_at, client=customer
            )

    def test_cancel_appointment(self):
        # create the appointment
        product = Product(
            identifier="2e656741-db4d-4c75-ae57-97fda6ce5ce8", name=""
        )  # all fields are hidden except the date of birth
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

        appointment_id = self.plugin.create_appointment(
            products=[product], location=location, start_at=start_at, client=customer
        )

        # delete it
        self.plugin.delete_appointment(appointment_id)

        # make sure it's been updated
        self.plugin.get_appointment_details(appointment_id)
