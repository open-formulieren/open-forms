from unittest.mock import patch

from django.test import RequestFactory, TestCase

from openforms.formio.service import get_dynamic_configuration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.tests.factories import SubmissionStepFactory

from .. import prefill_variables

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
