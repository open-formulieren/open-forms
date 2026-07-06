from unittest.mock import MagicMock, patch

from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.contrib.camunda.tests.utils import CamundaMixin
from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormVariableFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..models import Submission

# TODO
# Update tests when the frontend part has been merged (would be nice to have e2e tests too)


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SingleStepFormTests(APITestCase):
    @patch("openforms.submissions.api.viewsets.prefill_variables")
    def test_single_step_form_flow(self, m: MagicMock):
        endpoint = reverse_lazy("api:submission-list")
        form = FormFactory.create(generate_minimal_setup=True, is_single_step_form=True)
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # 1. create the submission
        submission_body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
            "initialDataReference": "of-or-3452fre3",
        }

        submission_response = self.client.post(
            endpoint, submission_body, headers={"Host": "testserver.com"}
        )
        submission = Submission.objects.get()
        form_step = form.formstep_set.get()

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)

        # 2. submit step data
        submit_data_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        submit_data = {"data": {"test-key-0": "foo"}}
        submit_data_response = self.client.put(
            submit_data_endpoint, submit_data, headers={"Host": "testserver.com"}
        )

        self.assertEqual(submit_data_response.status_code, status.HTTP_201_CREATED)

        # 3. complete form
        complete_submission_endpoint = reverse(
            "api:submission-complete",
            kwargs={"uuid": submission.uuid},
        )
        complete_data = {
            "privacy_policy_accepted": True,
            "statementOfTruthAccepted": False,
        }
        complete_submission_response = self.client.post(
            complete_submission_endpoint,
            complete_data,
            headers={"Host": "testserver.com"},
        )

        self.assertEqual(complete_submission_response.status_code, status.HTTP_200_OK)

        # 4. make sure the prefill was not called
        m.assert_not_called()

    def test_single_step_form_with_logic_and_variable_action(self):
        endpoint = reverse_lazy("api:submission-list")
        form = FormFactory.create(
            generate_minimal_setup=True,
            is_single_step_form=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textField",
                        "label": "Textfield",
                    },
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "Checkbox",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="test",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "checkbox"},
                    True,
                ]
            },
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": {"var": "textField"},
                    },
                    "variable": "test",
                    "component": "",
                }
            ],
        )

        form.apply_logic_analysis()

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # 1. create the submission
        submission_body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
        }

        submission_response = self.client.post(
            endpoint, submission_body, headers={"Host": "testserver.com"}
        )
        submission = Submission.objects.get()
        form_step = form.formstep_set.get()

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)

        # 2. submit step data
        submit_data_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        submit_data = {"data": {"textField": "foo", "checkbox": True}}
        submit_data_response = self.client.put(
            submit_data_endpoint, submit_data, headers={"Host": "testserver.com"}
        )

        self.assertEqual(submit_data_response.status_code, status.HTTP_201_CREATED)

        # 3. complete form
        complete_submission_endpoint = reverse(
            "api:submission-complete",
            kwargs={"uuid": submission.uuid},
        )
        complete_data = {
            "privacy_policy_accepted": True,
            "statementOfTruthAccepted": False,
        }
        complete_submission_response = self.client.post(
            complete_submission_endpoint,
            complete_data,
            headers={"Host": "testserver.com"},
        )

        self.assertEqual(complete_submission_response.status_code, status.HTTP_200_OK)

        # 4. make sure the submission value variables are correctly updated
        variables_data = submission.variables_state.get_data()
        expected = {"textField": "foo", "checkbox": True, "test": "foo"}

        self.assertEqual(variables_data, expected)

    def test_single_step_form_with_substr_and_variable_action(self):
        endpoint = reverse_lazy("api:submission-list")
        form = FormFactory.create(
            generate_minimal_setup=True,
            is_single_step_form=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textField",
                        "label": "Textfield",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="department",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "department",
                    "action": {
                        "type": "variable",
                        "value": {
                            "if": [
                                {
                                    "==": [
                                        {"substr": [{"var": "form_url.page"}, 0, 1]},
                                        "/",
                                    ]
                                },
                                "a@example.com",
                                "b@example.com",
                            ]
                        },
                    },
                }
            ],
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # 1. create the submission
        submission_body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
            "initialDataReference": "of-or-3452fre3",
        }

        submission_response = self.client.post(
            endpoint, submission_body, HTTP_HOST="testserver.com"
        )
        submission = Submission.objects.get()
        form_step = form.formstep_set.get()

        submission.form.apply_logic_analysis()

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)

        # 2. submit step data
        submit_data_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        submit_data = {"data": {"textField": "foo"}}
        submit_data_response = self.client.put(
            submit_data_endpoint, submit_data, HTTP_HOST="testserver.com"
        )

        self.assertEqual(submit_data_response.status_code, status.HTTP_201_CREATED)

        # 3. complete form
        complete_submission_endpoint = reverse(
            "api:submission-complete",
            kwargs={"uuid": submission.uuid},
        )
        complete_data = {
            "privacy_policy_accepted": True,
            "statementOfTruthAccepted": False,
        }
        complete_submission_response = self.client.post(
            complete_submission_endpoint, complete_data, HTTP_HOST="testserver.com"
        )

        self.assertEqual(complete_submission_response.status_code, status.HTTP_200_OK)

        # 4. make sure the submission value variables are correctly updated
        variables_data = submission.variables_state.get_data()
        expected = {"textField": "foo", "department": "a@example.com"}

        self.assertEqual(variables_data, expected)


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SingleStepFormVCRTests(CamundaMixin, OFVCRMixin, APITestCase):
    def test_single_step_form_with_logic_and_dmn_action(self):
        endpoint = reverse_lazy("api:submission-list")
        form = FormFactory.create(
            generate_minimal_setup=True,
            is_single_step_form=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "invoiceAmount",
                        "label": "Invoice Amount",
                    },
                    {
                        "type": "textfield",
                        "key": "textField",
                        "label": "Textfield",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="test",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "component": "",
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "camunda7",
                            "decision_definition_id": "invoiceClassification",
                            "decision_definition_version": "2",
                            "input_mapping": [
                                {
                                    "form_variable": "invoiceAmount",
                                    "dmn_variable": "amount",
                                },
                                {
                                    "form_variable": "textField",
                                    "dmn_variable": "invoiceCategory",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "test",
                                    "dmn_variable": "invoiceClassification",
                                }
                            ],
                        },
                    },
                }
            ],
        )

        form.apply_logic_analysis()

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # 1. create the submission
        submission_body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
        }

        submission_response = self.client.post(
            endpoint, submission_body, headers={"Host": "testserver.com"}
        )
        submission = Submission.objects.get()
        form_step = form.formstep_set.get()

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)

        # 2. submit step data
        submit_data_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        submit_data = {"data": {"textField": "Misc", "invoiceAmount": 100}}
        submit_data_response = self.client.put(
            submit_data_endpoint, submit_data, headers={"Host": "testserver.com"}
        )

        self.assertEqual(submit_data_response.status_code, status.HTTP_201_CREATED)

        # 3. complete form
        complete_submission_endpoint = reverse(
            "api:submission-complete",
            kwargs={"uuid": submission.uuid},
        )
        complete_data = {
            "privacy_policy_accepted": True,
            "statementOfTruthAccepted": False,
        }
        complete_submission_response = self.client.post(
            complete_submission_endpoint,
            complete_data,
            headers={"Host": "testserver.com"},
        )

        self.assertEqual(complete_submission_response.status_code, status.HTTP_200_OK)

        # 4. make sure the submission value variables are correctly updated
        variables_data = submission.variables_state.get_data()
        expected = {
            "invoiceAmount": 100,
            "textField": "Misc",
            "test": "day-to-day expense",
        }

        self.assertEqual(variables_data, expected)
