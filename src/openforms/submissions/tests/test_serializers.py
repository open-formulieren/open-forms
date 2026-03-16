from django.test import TestCase, tag

from openforms.forms.tests.factories import (
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ..api.serializers import SubmissionStepSerializer
from .factories import SubmissionFactory


class SubmissionStepSerializerTests(TestCase):
    @tag("gh-6068")
    def test_formio_validation_does_not_use_outdated_configuration_and_or_values(self):
        step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                    {
                        "type": "number",
                        "key": "number",
                        "label": "number",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=step.form,
            user_defined=True,
            key="user_defined",
            data_type=FormVariableDataTypes.string,
            initial_value="Initial value",
        )

        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={"!=": [{"var": "textfield"}, "foo"]},
            actions=[
                {
                    "action": {
                        "name": "Hide number",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "number",
                },
            ],
        )
        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={"==": [{"var": "number"}, None]},
            actions=[
                {
                    "action": {
                        "name": "Set variable value",
                        "type": "variable",
                        "value": "I shouldn't be set!",
                    },
                    "variable": "user_defined",
                },
            ],
        )
        submission = SubmissionFactory.create(form=step.form)

        # Execute validation
        execution_state = submission.load_execution_state()
        submission_step = execution_state.get_submission_step(str(step.uuid))
        serializer = SubmissionStepSerializer(
            instance=submission_step, data={"data": {"textfield": "foo", "number": 42}}
        )
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid)

        # Ensure state and configuration are not mutated in an unexpected way.
        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_unsaved=True)
        self.assertEqual(
            {"textfield": "foo", "number": 42, "user_defined": "Initial value"},
            data.data,
        )
        self.assertEqual(
            {
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                    {
                        "type": "number",
                        "key": "number",
                        "label": "number",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ]
            },
            submission_step.form_step.form_definition.configuration,
        )
