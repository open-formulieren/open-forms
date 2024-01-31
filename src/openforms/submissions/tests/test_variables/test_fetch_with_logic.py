from pathlib import Path

import requests_mock
from factory.django import FileField
from freezegun import freeze_time
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormLogicFactory
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..factories import SubmissionFactory
from ..mixins import SubmissionsMixin


class ServiceFetchWithActionsTest(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="https://httpbin.org/",
            auth_type=AuthTypes.no_auth,
            oas_file=FileField(
                from_path=str(Path(__file__).parent.parent / "files" / "openapi.yaml")
            ),
        )

    @requests_mock.Mocker(case_sensitive=True)
    def test_it_calls_service_for_the_answer(self, m):
        submission = SubmissionFactory.from_components(
            [{"type": "number", "key": "someField"}]
        )
        fetch_config = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get"
        )

        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "someField",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                        "value": fetch_config.id,
                    },
                }
            ],
        )
        self._add_submission_to_session(submission)
        m.get("https://httpbin.org/get", json=42)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        response = self.client.post(endpoint, data={"data": {"someField": None}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["step"]["data"], {"someField": 42})

    @requests_mock.Mocker(case_sensitive=True)
    def test_it_handles_bad_service_responses(self, m):
        submission = SubmissionFactory.from_components(
            [{"type": "number", "key": "someField"}]
        )
        fetch_config = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get"
        )

        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "someField",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                        "value": fetch_config.id,
                    },
                }
            ],
        )
        self._add_submission_to_session(submission)

        m.get("https://httpbin.org/get", status_code=500)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        response = self.client.post(endpoint, data={"data": {"someField": None}})

        self.assertEqual(response.status_code, 200)
        # assert no new value
        # if a prefill service is down or misconfigured, a submitter's values
        # shouldn't be overwritten
        self.assertEqual(response.data["step"]["data"], {})

    @requests_mock.Mocker(case_sensitive=True)
    def test_requests_not_made_multiple_times(self, m):
        submission = SubmissionFactory.from_components(
            [
                {"type": "textfield", "key": "fieldA"},
                {"type": "textfield", "key": "fieldB"},
                {"type": "textfield", "key": "fieldC"},
            ]
        )
        fetch_config1 = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get"
        )
        fetch_config2 = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get", query_params={"fieldC": ["{{ fieldC }}"]}
        )

        FormLogicFactory.create(
            form=submission.form,
            order=1,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "fieldA",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                        "value": fetch_config1.id,
                    },
                }
            ],
        )
        FormLogicFactory.create(
            form=submission.form,
            order=2,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "fieldB",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                        "value": fetch_config2.id,
                    },
                }
            ],
        )

        self._add_submission_to_session(submission)

        m.get("https://httpbin.org/get", json=42)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        response = self.client.post(endpoint, data={"data": {"fieldC": 42}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(m.request_history), 2)
        self.assertEqual(m.request_history[-1].url, "https://httpbin.org/get?fieldC=42")
        self.assertEqual(m.request_history[-2].url, "https://httpbin.org/get")

        response = self.client.post(endpoint, data={"data": {"fieldC": 43}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(m.request_history), 3)
        self.assertEqual(m.request_history[-1].url, "https://httpbin.org/get?fieldC=43")

    @requests_mock.Mocker(case_sensitive=True)
    def test_requests_cache_timeout(self, m):
        submission = SubmissionFactory.from_components(
            [
                {"type": "textfield", "key": "fieldA"},
            ]
        )
        fetch_config = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get", cache_timeout=30
        )

        FormLogicFactory.create(
            form=submission.form,
            order=1,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "fieldA",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                        "value": fetch_config.id,
                    },
                }
            ],
        )

        self._add_submission_to_session(submission)

        m.get("https://httpbin.org/get", json=42)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.first().uuid,
            },
        )

        with freeze_time("2023-02-21T18:00:00Z"):
            response = self.client.post(endpoint, data={"data": {}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(m.request_history), 1)
        self.assertEqual(m.request_history[-1].url, "https://httpbin.org/get")

        with freeze_time("2023-02-21T18:01:00Z"):
            response = self.client.post(endpoint, data={"data": {}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(m.request_history), 2)
        self.assertEqual(m.request_history[-1].url, "https://httpbin.org/get")
