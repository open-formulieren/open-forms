from pathlib import Path

import requests_mock
from factory.django import FileField
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormLogicFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
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
