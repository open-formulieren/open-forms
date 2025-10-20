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
from ..plugin import PLUGIN_IDENTIFIER
from ..typing import SupportedChannels


class CommunicationPreferencesTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        customer_interactions_config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        profile_channels: list[SupportedChannels] = ["email", "phone_number"]
        cls.form = FormFactory.create(
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
            form=cls.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": customer_interactions_config.identifier,
                "profile_form_variable": "profile",
            },
        )

    def test_prefill_values_found(self):
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=self.form,
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
        submission = SubmissionFactory.create(
            auth_info__value="123456780",
            auth_info__attribute=AuthAttribute.bsn,
            form=self.form,
        )
        assert submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["communication-preferences"].value, {})

    def test_prefill_values_not_authenticated(self):
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["communication-preferences"].value, {})
