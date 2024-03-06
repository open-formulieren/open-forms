from pathlib import Path

from django.test import TestCase

import requests_mock
from factory.django import FileField
from zgw_consumers.constants import APITypes, AuthTypes

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormLogicFactory, FormVariableFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory


class ServiceFetchWithActionsTest(TestCase):
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
        submission = SubmissionFactory.from_components([])
        fetch_config = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get"
        )
        FormVariableFactory.create(
            key="someVariable",
            form=submission.form,
            service_fetch_configuration=fetch_config,
        )

        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "someVariable",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                    },
                }
            ],
        )
        m.get("https://httpbin.org/get", json=42)

        evaluate_form_logic(
            submission, submission.submissionstep_set.first(), submission.data
        )

        state = submission.load_submission_value_variables_state()

        variable = state.get_variable("someVariable")

        self.assertEqual(variable.value, 42)

    @requests_mock.Mocker(case_sensitive=True)
    def test_it_handles_bad_service_responses(self, m):
        submission = SubmissionFactory.from_components([])
        fetch_config = ServiceFetchConfigurationFactory.create(
            service=self.service, path="get"
        )
        FormVariableFactory.create(
            key="someVariable",
            form=submission.form,
            service_fetch_configuration=fetch_config,
            initial_value="some initial value",
        )

        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "someVariable",
                    "action": {
                        "name": "Fetch some field from some server",
                        "type": LogicActionTypes.fetch_from_service,
                    },
                }
            ],
        )

        m.get("https://httpbin.org/get", status_code=500)

        evaluate_form_logic(
            submission, submission.submissionstep_set.first(), submission.data
        )

        state = submission.load_submission_value_variables_state(refresh=True)

        variable = state.get_variable("someVariable")
        # assert no new value
        # if a fetch service is down or misconfigured, a submitter's values
        # shouldn't be overwritten
        self.assertEqual(variable.value, "some initial value")
