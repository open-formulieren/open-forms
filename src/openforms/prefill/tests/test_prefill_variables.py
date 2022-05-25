from unittest.mock import patch

from django.test import TestCase

from openforms.forms.tests.factories import FormStepFactory, FormVariableFactory
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.tests.factories import SubmissionFactory

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
        FormVariableFactory.create(
            form=form_step.form,
            form_definition=form_step.form_definition,
            key="voornamen",
            prefill_plugin="demo",
            prefill_attribute="random_string",
            source="component",
        )
        FormVariableFactory.create(
            form=form_step.form,
            form_definition=form_step.form_definition,
            key="age",
            prefill_plugin="demo",
            prefill_attribute="random_number",
            source="component",
        )
        submission = SubmissionFactory.create(form=form_step.form)

        prefill_variables(submission=submission)

        submission_value_variables_state = (
            submission.load_submission_value_variables_state()
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
