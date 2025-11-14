
from django.test import TestCase

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.forms.tests.factories import FormVariableFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ....service import prefill_variables
from ..plugin import PLUGIN_IDENTIFIER


class CommunicationPreferencesTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_prefill_values_found(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "profile",
                    "type": "customerProfile",
                    "label": "Profile",
                },
            ],
        )
        assert submission.is_authenticated

        FormVariableFactory.create(
            key="communication-preferences",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.config.identifier,
                "profile_form_variable": "profile",
            }
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected = {
            "emails": [
                "someemail@example.org",
                "devilkiller@example.org",
                "john.smith@gmail.com",
            ],
            "preferred_email": "john.smith@gmail.com",
            "phone_numbers": ["0687654321", "0612345678"],
            "preferred_phone_number": "0612345678",
        }
        self.assertEqual(state.variables["communication-preferences"].value, expected)

    def test_prefill_values_not_found(self):
        submission = SubmissionFactory.create(auth_info__value="123456780")
        assert submission.is_authenticated
        FormVariableFactory.create(
            key="profile_prefill",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "email": True,
                "phone_number": True,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["profile_prefill"].value, {})

    def test_prefill_values_not_authenticated(self):
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated
        FormVariableFactory.create(
            key="profile_prefill",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "email": True,
                "phone_number": True,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["profile_prefill"].value, {})



