from django.test import TestCase, tag

from openforms.formio.typing.custom import DigitalAddress, SupportedChannels
from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.contrib.customer_interactions.plugin import PLUGIN_IDENTIFIER
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..client import get_customer_interactions_client
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
        partij_uuid = result["partij_uuid"]

        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertIsNone(betrokkene["wasPartij"])
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
        self.assertEqual(partij_uuid, "")

        self.assertEqual(len(digital_addresses["created"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
        ]

        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["created"], expected_address
                )

        self.assertEqual(len(digital_addresses["updated"]), 0)

    def test_auth_with_bsn_user_not_known_in_openklant(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {
                "address": "some@email.com",
                "type": "email",
                "preferenceUpdate": "useOnlyOnce",
            },
            {
                "address": "0612345678",
                "type": "phoneNumber",
                "preferenceUpdate": "isNewPreferred",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            bsn="108915864",
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
        partij_uuid = result["partij_uuid"]
        digital_addresses = result["digital_addresses"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_bsn("108915864")

        # check that party is linked to the user
        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )
        self.assertEqual(
            betrokkene["wasPartij"], {"url": party["url"], "uuid": partij_uuid}
        )

        self.assertEqual(len(digital_addresses["created"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": {"url": party["url"], "uuid": partij_uuid},
            },
        ]
        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["created"], expected_address
                )

        self.assertEqual(len(digital_addresses["updated"]), 0)

    def test_auth_with_bsn_user_known_in_openklant_new_address(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {
                "address": "some@email.com",
                "type": "email",
                "preferenceUpdate": "useOnlyOnce",
            },
            {
                "address": "0611111111",
                "type": "phoneNumber",
                "preferenceUpdate": "isNewPreferred",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            bsn="123456782",
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
        prefill_variables(submission=submission)

        result = update_customer_interaction_data(submission, "profile")

        klantcontact = result["klantcontact"]
        betrokkene = result["betrokkene"]
        onderwerpobject = result["onderwerpobject"]
        digital_addresses = result["digital_addresses"]
        partij_uuid = result["partij_uuid"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_bsn("123456782")

        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )

        self.assertEqual(
            betrokkene["wasPartij"],
            {"url": party["url"], "uuid": partij_uuid},
        )

        self.assertEqual(len(digital_addresses["created"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
            {
                "adres": "0611111111",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": {
                    "url": party["url"],
                    "uuid": partij_uuid,
                },
            },
        ]
        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["created"], expected_address
                )

        self.assertEqual(len(digital_addresses["updated"]), 0)

    def test_auth_with_bsn_user_known_in_openklant_known_addresses(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        # both addresses are known in the Open Klant
        profile_data: list[DigitalAddress] = [
            {
                "address": "someemail@example.org",
                "type": "email",
            },
            {
                "address": "0687654321",
                "type": "phoneNumber",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            bsn="123456782",
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
        prefill_variables(submission=submission)

        result = update_customer_interaction_data(submission, "profile")

        klantcontact = result["klantcontact"]
        betrokkene = result["betrokkene"]
        onderwerpobject = result["onderwerpobject"]
        digital_addresses = result["digital_addresses"]
        partij_uuid = result["partij_uuid"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_bsn("123456782")

        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )

        self.assertEqual(
            betrokkene["wasPartij"],
            {"url": party["url"], "uuid": partij_uuid},
        )

        # no new address is added
        self.assertEqual(digital_addresses["created"], [])
        self.assertEqual(digital_addresses["updated"], [])

    def test_auth_with_bsn_user_known_in_openklant_known_addresses_with_different_preference(
        self,
    ):
        """
        even if we change the preference for the known address - we don't update it
        """
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        # both addresses are known in the Open Klant and both are not preferred
        profile_data: list[DigitalAddress] = [
            {
                "address": "devilkiller@example.org",
                "type": "email",
                "preferenceUpdate": "isNewPreferred",
            },
            {
                "address": "0687654321",
                "type": "phoneNumber",
                "preferenceUpdate": "isNewPreferred",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            bsn="123456782",
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
        prefill_variables(submission=submission)

        result = update_customer_interaction_data(submission, "profile")

        klantcontact = result["klantcontact"]
        betrokkene = result["betrokkene"]
        onderwerpobject = result["onderwerpobject"]
        digital_addresses = result["digital_addresses"]
        partij_uuid = result["partij_uuid"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_bsn("123456782")

        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )

        self.assertEqual(
            betrokkene["wasPartij"],
            {"url": party["url"], "uuid": partij_uuid},
        )

        # no new address is added
        self.assertEqual(digital_addresses["created"], [])
        # 2 addresses are updated
        self.assertEqual(len(digital_addresses["updated"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "devilkiller@example.org",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": True,
                "verstrektDoorPartij": {
                    "url": party["url"],
                    "uuid": partij_uuid,
                },
            },
            {
                "adres": "0687654321",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
                "verstrektDoorPartij": {
                    "url": party["url"],
                    "uuid": partij_uuid,
                },
            },
        ]
        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["updated"], expected_address
                )

    def test_auth_with_kvk_organization_not_known_in_openklant(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {
                "address": "some@email.com",
                "type": "email",
                "preferenceUpdate": "useOnlyOnce",
            },
            {
                "address": "0612345678",
                "type": "phoneNumber",
                "preferenceUpdate": "isNewPreferred",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            kvk="11122233",
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
        partij_uuid = result["partij_uuid"]
        digital_addresses = result["digital_addresses"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_kvk("11122233")

        # check that party is linked to the organization
        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )
        self.assertEqual(
            betrokkene["wasPartij"], {"url": party["url"], "uuid": partij_uuid}
        )

        self.assertEqual(len(digital_addresses["created"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": {"url": party["url"], "uuid": partij_uuid},
            },
        ]
        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["created"], expected_address
                )

        self.assertEqual(len(digital_addresses["updated"]), 0)

    def test_auth_with_kvk_organization_known_in_openklant_new_address(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {
                "address": "some@email.com",
                "type": "email",
                "preferenceUpdate": "useOnlyOnce",
            },
            {
                "address": "0611111111",
                "type": "phoneNumber",
                "preferenceUpdate": "isNewPreferred",
            },
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
            public_registration_reference="OF-12346",
            form__name="With profile",
            kvk="12345678",
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
        prefill_variables(submission=submission)

        result = update_customer_interaction_data(submission, "profile")

        klantcontact = result["klantcontact"]
        betrokkene = result["betrokkene"]
        onderwerpobject = result["onderwerpobject"]
        digital_addresses = result["digital_addresses"]
        partij_uuid = result["partij_uuid"]

        with get_customer_interactions_client(self.config) as client:
            party = client.find_party_for_kvk("12345678")

        self.assertEqual(party["uuid"], partij_uuid)
        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertEqual(klantcontact["onderwerp"], "With profile")
        self.assertEqual(betrokkene["rol"], "klant")
        self.assertTrue(betrokkene["initiator"])
        self.assertEqual(
            onderwerpobject["onderwerpobjectidentificator"],
            {
                "objectId": "OF-12346",
                "codeObjecttype": "formulierinzending",
                "codeRegister": "Open Formulieren",
                "codeSoortObjectId": "public_registration_reference",
            },
        )

        self.assertEqual(
            betrokkene["wasPartij"],
            {"url": party["url"], "uuid": partij_uuid},
        )

        self.assertEqual(len(digital_addresses["created"]), 2)
        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "some@email.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": None,
            },
            {
                "adres": "0611111111",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
                "verstrektDoorBetrokkene": {
                    "url": betrokkene["url"],
                    "uuid": betrokkene["uuid"],
                },
                "verstrektDoorPartij": {
                    "url": party["url"],
                    "uuid": partij_uuid,
                },
            },
        ]
        for expected_address in expected_addresses:
            with self.subTest(expected_address):
                self.assertAddressPresent(
                    digital_addresses["created"], expected_address
                )

        self.assertEqual(len(digital_addresses["updated"]), 0)

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

    @tag("gh-5875")
    def test_empty_address(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        profile_data: list[DigitalAddress] = [
            {"address": "some@email.com", "type": "email"},
            {"address": "", "type": "phoneNumber"},
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
        partij_uuid = result["partij_uuid"]

        self.assertEqual(klantcontact["kanaal"], "Webformulier")
        self.assertIsNone(betrokkene["wasPartij"])
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
        self.assertEqual(partij_uuid, "")

        self.assertEqual(len(digital_addresses["created"]), 1)
        expected_address: ExpectedDigitalAddress = {
            "adres": "some@email.com",
            "soortDigitaalAdres": "email",
            "isStandaardAdres": False,
            "verstrektDoorBetrokkene": {
                "url": betrokkene["url"],
                "uuid": betrokkene["uuid"],
            },
            "verstrektDoorPartij": None,
        }

        self.assertAddressPresent(digital_addresses["created"], expected_address)

        self.assertEqual(len(digital_addresses["updated"]), 0)
