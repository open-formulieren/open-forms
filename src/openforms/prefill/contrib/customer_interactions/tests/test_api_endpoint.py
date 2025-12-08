import uuid

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..plugin import PLUGIN_IDENTIFIER
from ..typing import SupportedChannels


class CommunicationPreferencesAPITests(OFVCRMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.customer_interactions_config = (
            CustomerInteractionsAPIGroupConfigFactory.create(
                for_test_docker_compose=True
            )
        )

    def test_api_endpoint_prefill_found(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
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
            data_type=FormVariableDataTypes.array,
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
        self._add_submission_to_session(submission)
        prefill_variables(submission=submission)

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={"submission_uuid": submission.uuid, "profile_component": "profile"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "type": "email",
                    "options": [
                        "someemail@example.org",
                        "devilkiller@example.org",
                        "john.smith@gmail.com",
                    ],
                    "preferred": "john.smith@gmail.com",
                },
                {
                    "type": "phoneNumber",
                    "options": ["0687654321", "0612345678"],
                    "preferred": "0612345678",
                },
            ],
        )

    def test_api_endpoint_no_user_var(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
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
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        self._add_submission_to_session(submission)
        prefill_variables(submission=submission)

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={"submission_uuid": submission.uuid, "profile_component": "profile"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_api_endpoint_only_email(self):
        profile_channels: list[SupportedChannels] = ["email"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "emailProfile",
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
            data_type=FormVariableDataTypes.array,
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
        self._add_submission_to_session(submission)
        prefill_variables(submission=submission)

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={
                "submission_uuid": submission.uuid,
                "profile_component": "emailProfile",
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "type": "email",
                    "options": [
                        "someemail@example.org",
                        "devilkiller@example.org",
                        "john.smith@gmail.com",
                    ],
                    "preferred": "john.smith@gmail.com",
                },
            ],
        )

    def test_api_endpoint_prevent_access_to_others_submissions(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
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
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={"submission_uuid": submission.uuid, "profile_component": "profile"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_endpoint_non_existing_submission(self):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={"submission_uuid": uuid.uuid4(), "profile_component": "profile"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_endpoint_dots_in_var_key(self):
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "customer.profile",
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
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": self.customer_interactions_config.identifier,
                "profile_form_variable": "customer.profile",
            },
        )
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            form=form,
        )
        self._add_submission_to_session(submission)
        prefill_variables(submission=submission)

        url = reverse(
            "api:prefill_customer_interactions:communication-preferences",
            kwargs={
                "submission_uuid": submission.uuid,
                "profile_component": "customer.profile",
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "type": "email",
                    "options": [
                        "someemail@example.org",
                        "devilkiller@example.org",
                        "john.smith@gmail.com",
                    ],
                    "preferred": "john.smith@gmail.com",
                },
                {
                    "type": "phoneNumber",
                    "options": ["0687654321", "0612345678"],
                    "preferred": "0612345678",
                },
            ],
        )
