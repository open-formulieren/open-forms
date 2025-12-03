from django.test import TestCase

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ....service import prefill_variables
from ..constants import PLUGIN_IDENTIFIER
from ..typing import SupportedChannels


class CommunicationPreferencesTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.customer_interactions_config = (
            CustomerInteractionsAPIGroupConfigFactory.create(
                for_test_docker_compose=True
            )
        )

    def test_prefill_values_found(self):
        profile_channels: list[SupportedChannels] = ["email", "phone_number"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "profile",
                        "type": "customerProfile",
                        "label": "Profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="communication-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "profile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected = {
            "email": {
                "options": [
                    "someemail@example.org",
                    "devilkiller@example.org",
                    "john.smith@gmail.com",
                ],
                "preferred": "john.smith@gmail.com",
            },
            "phone_number": {
                "options": ["0687654321", "0612345678"],
                "preferred": "0612345678",
            },
        }
        self.assertEqual(state.variables["communication-preferences"].value, expected)

    def test_prefill_values_not_found(self):
        profile_channels: list[SupportedChannels] = ["email", "phone_number"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "profile",
                        "type": "customerProfile",
                        "label": "Profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="communication-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "profile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456780",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["communication-preferences"].value, {})

    def test_prefill_values_not_authenticated(self):
        profile_channels: list[SupportedChannels] = ["email", "phone_number"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "profile",
                        "type": "customerProfile",
                        "label": "Profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="communication-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "profile",
            },
        )
        submission = SubmissionFactory.create(form=form)
        assert not submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["communication-preferences"].value, {})

    def test_prefill_values_for_email(self):
        profile_channels: list[SupportedChannels] = ["email"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "emailProfile",
                        "type": "customerProfile",
                        "label": "Email profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="email-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "emailProfile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected = {
            "email": {
                "options": [
                    "someemail@example.org",
                    "devilkiller@example.org",
                    "john.smith@gmail.com",
                ],
                "preferred": "john.smith@gmail.com",
            },
        }
        self.assertEqual(state.variables["email-preferences"].value, expected)

    def test_prefill_values_for_phone_number(self):
        profile_channels: list[SupportedChannels] = ["phone_number"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "phoneNumberProfile",
                        "type": "customerProfile",
                        "label": "Phone Number profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="phone-number-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "phoneNumberProfile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected = {
            "phone_number": {
                "options": ["0687654321", "0612345678"],
                "preferred": "0612345678",
            },
        }
        self.assertEqual(state.variables["phone-number-preferences"].value, expected)

    def test_prefill_values_no_channel(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "EmptyProfile",
                        "type": "customerProfile",
                        "label": "Empty profile",
                        "digitalAddressTypes": [],
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        FormVariableFactory.create(
            key="empty-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "EmptyProfile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["empty-preferences"].value, {})
