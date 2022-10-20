from unittest.mock import patch

from django.test import RequestFactory, TestCase

import requests_mock

from openforms.authentication.constants import AuthAttribute
from openforms.formio.service import get_dynamic_configuration
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import FormStepFactory
from openforms.logging.models import TimelineLogProxy
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.tests.factories import SubmissionStepFactory

from .. import prefill_variables
from ..contrib.haalcentraal.models import HaalCentraalConfig
from ..contrib.haalcentraal.tests.utils import load_binary_mock

CONFIGURATION = {
    "display": "form",
    "components": [
        {
            "key": "voornamen",
            "type": "textfield",
            "label": "Voornamen",
            "prefill": {
                "plugin": "demo",
                "attribute": "random_string",
            },
            "multiple": False,
        },
        {
            "key": "age",
            "type": "number",
            "label": "Age",
            "prefill": {
                "plugin": "demo",
                "attribute": "random_number",
            },
            "multiple": False,
        },
    ],
}


class PrefillVariablesTests(TestCase):
    @patch(
        "openforms.prefill._fetch_prefill_values",
        return_value={
            "demo": {"random_string": "Not so random string", "random_number": 123}
        },
    )
    def test_applying_prefill_plugins(self, m_prefill):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form, form_step=form_step
        )

        prefill_variables(submission=submission_step.submission)

        submission_value_variables_state = (
            submission_step.submission.load_submission_value_variables_state()
        )

        self.assertEqual(2, len(submission_value_variables_state.variables))

        submission_variable1 = submission_value_variables_state.get_variable(
            key="voornamen"
        )
        submission_variable2 = submission_value_variables_state.get_variable(key="age")

        self.assertEqual("Not so random string", submission_variable1.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable1.source
        )
        self.assertEqual(123, submission_variable2.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable2.source
        )

    @patch(
        "openforms.prefill._fetch_prefill_values",
        return_value={"postcode": {"static": "1015CJ"}},
    )
    def test_normalization_applied(self, m_prefill):
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                        "prefill": {
                            "plugin": "postcode",
                            "attribute": "static",
                        },
                        "defaultValue": "",
                    }
                ]
            }
        )
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
        )

        prefill_variables(submission=submission_step.submission)

        request = RequestFactory().get("/foo")
        configuration = get_dynamic_configuration(
            submission_step.form_step.form_definition.configuration,
            request=request,
            submission=submission_step.submission,
        )

        component = configuration["components"][0]
        self.assertEqual(component["type"], "postcode")
        self.assertEqual(component["defaultValue"], "1015 CJ")

    @requests_mock.Mocker()
    @patch("openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo")
    def test_no_success_message_on_failure(self, m, m_solo):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=404,
        )

        service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config = HaalCentraalConfig(service=service)
        m_solo.return_value = config

        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                        "prefill": {
                            "plugin": "haalcentraal",
                            "attribute": "test-field",
                        },
                        "defaultValue": "",
                    }
                ]
            }
        )
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
        )

        prefill_variables(submission=submission_step.submission)

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)

        for log in logs:
            self.assertNotEqual(log.event, "prefill_retrieve_success")

    def test_prefill_variables_are_retrieved_when_form_variables_deleted(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
            data={"voornamen": "", "age": None},
        )

        submission_value_variables_state = (
            submission_step.submission.load_submission_value_variables_state()
        )
        submission_value_variables_state.variables

        FormVariable.objects.all().delete()

        prefill_variables = submission_value_variables_state.get_prefill_variables()
        self.assertEqual(2, len(prefill_variables))
