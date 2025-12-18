from django.test import TestCase

from openforms.formio.typing.custom import DigitalAddress, SupportedChannels
from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.contrib.customer_interactions.plugin import PLUGIN_IDENTIFIER
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..update import update_customer_interaction_data
from .mixins import CustomerInteractionsMixin
from .typing import ExpectedDigitalAddress


class UpdateCustomerInteractionDataTests(
    CustomerInteractionsMixin, OFVCRMixin, TestCase
):
    def test_non_auth_user(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {"address": "some@email.com", "type": "email"},
            {"address": "0612345678", "type": "phoneNumber"},
        ]
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "profile",
                    "type": "customerProfile",
                    "label": "Profile",
                    "digitalAddressTypes": profile_channels,
                    "shouldUpdateCustomerData": True,
                }
            ],
            submitted_data={
                "profile": profile_data,
            },
            public_registration_reference="OF-12345",
            form__name="With profile",
        )
        FormVariableFactory.create(
            key="communication-preferences",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.config.identifier,
                "profile_form_variable": "profile",
            },
        )

        result = update_customer_interaction_data(submission, "profile")

        klantcontact = result["klantcontact"]
        betrokkene = result["betrokkene"]
        onderwerpobject = result["onderwerpobject"]
        digital_addresses = result["digital_addresses"]

        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12345",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )

        self.assertEqual(len(digital_addresses), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
            },
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": False,
            },
        ]

        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(digital_addresses, expected_address)

    def test_no_prefill_var_configured(self):
        """
        without prefill config Customer Interactions API can't be updated
        """
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {"address": "some@email.com", "type": "email"},
            {"address": "0612345678", "type": "phoneNumber"},
        ]
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "profile",
                    "type": "customerProfile",
                    "label": "Profile",
                    "digitalAddressTypes": profile_channels,
                    "shouldUpdateCustomerData": True,
                }
            ],
            submitted_data={
                "profile": profile_data,
            },
        )
        result = update_customer_interaction_data(submission, "profile")

        self.assertIsNone(result)
