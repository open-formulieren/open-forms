from unittest.mock import patch

import requests_mock
from django_camunda.models import CamundaConfig
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormLogicFactory

from ..factories import SubmissionFactory
from ..mixins import SubmissionsMixin


@requests_mock.Mocker()
class TestCacheDMNRequests(SubmissionsMixin, APITestCase):

    def test_requests_not_made_multiple_times(self, m):
        submission = SubmissionFactory.from_components(
            [
                {"type": "textfield", "key": "fieldA"},
                {"type": "textfield", "key": "fieldB"},
                {"type": "textfield", "key": "fieldC"},
            ]
        )

        FormLogicFactory.create(
            form=submission.form,
            order=1,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "fieldA",
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "camunda7",
                            "decision_definition_id": "some-id",
                            "decision_definition_version": "1",
                            "input_mapping": [
                                {
                                    "form_variable": "fieldA",
                                    "dmn_variable": "fieldADMN",
                                },
                                {
                                    "form_variable": "fieldB",
                                    "dmn_variable": "fieldBDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "fieldC",
                                    "dmn_variable": "fieldCDMN",
                                }
                            ],
                        },
                    },
                }
            ],
        )

        self._add_submission_to_session(submission)

        m.get(
            "https://camunda.example.com/engine-rest/decision-definition?key=some-id&version=1",
            json=[{"id": "some-id:blabla"}],
        )
        m.post(
            "https://camunda.example.com/engine-rest/decision-definition/some-id:blabla/evaluate",
            json=[
                {"fieldCDMN": {"type": "String", "value": "a-result", "valueInfo": {}}}
            ],
        )

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        config = CamundaConfig(
            enabled=True,
            root_url="https://camunda.example.com",
            rest_api_path="engine-rest/",
        )

        with patch(
            "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
            return_value=config,
        ):
            response = self.client.post(
                endpoint, data={"data": {"fieldA": "42", "fieldB": "43"}}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(m.request_history), 2)
            self.assertEqual(
                m.request_history[-1].url,
                "https://camunda.example.com/engine-rest/decision-definition/some-id:blabla/evaluate",
            )
            self.assertEqual(
                m.request_history[-2].url,
                "https://camunda.example.com/engine-rest/decision-definition?key=some-id&version=1",
            )

            response = self.client.post(
                endpoint, data={"data": {"fieldA": "42", "fieldB": "43"}}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(m.request_history), 2)

            response = self.client.post(
                endpoint, data={"data": {"fieldA": "44", "fieldB": "45"}}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(m.request_history), 4)

    def test_requests_not_made_multiple_times_with_non_serialiseable_vars(self, m):
        submission = SubmissionFactory.from_components(
            [
                {"type": "date", "key": "fieldA", "multiple": True},
                {"type": "datetime", "key": "fieldB"},
                {"type": "textfield", "key": "fieldC"},
            ]
        )

        FormLogicFactory.create(
            form=submission.form,
            order=1,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "fieldA",
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "camunda7",
                            "decision_definition_id": "some-id",
                            "decision_definition_version": "1",
                            "input_mapping": [
                                {
                                    "form_variable": "fieldA",
                                    "dmn_variable": "fieldADMN",
                                },
                                {
                                    "form_variable": "fieldB",
                                    "dmn_variable": "fieldBDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "fieldC",
                                    "dmn_variable": "fieldCDMN",
                                }
                            ],
                        },
                    },
                }
            ],
        )

        self._add_submission_to_session(submission)

        m.get(
            "https://camunda.example.com/engine-rest/decision-definition?key=some-id&version=1",
            json=[{"id": "some-id:blabla"}],
        )
        m.post(
            "https://camunda.example.com/engine-rest/decision-definition/some-id:blabla/evaluate",
            json=[
                {"fieldCDMN": {"type": "String", "value": "a-result", "valueInfo": {}}}
            ],
        )

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        config = CamundaConfig(
            enabled=True,
            root_url="https://camunda.example.com",
            rest_api_path="engine-rest/",
        )

        with patch(
            "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
            return_value=config,
        ):
            response = self.client.post(
                endpoint,
                data={
                    "data": {
                        "fieldA": ["2020-01-01", "2021-01-01"],
                        "fieldB": "2022-02-21T00:00:00",
                    }
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(m.request_history), 2)
            self.assertEqual(
                m.request_history[-1].url,
                "https://camunda.example.com/engine-rest/decision-definition/some-id:blabla/evaluate",
            )
            self.assertEqual(
                m.request_history[-2].url,
                "https://camunda.example.com/engine-rest/decision-definition?key=some-id&version=1",
            )

            response = self.client.post(
                endpoint,
                data={
                    "data": {
                        "fieldA": ["2020-01-01", "2021-01-01"],
                        "fieldB": "2022-02-21T00:00:00",
                    }
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(m.request_history), 2)
