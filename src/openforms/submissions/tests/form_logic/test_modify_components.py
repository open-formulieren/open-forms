from django.test import TestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory


class FormLogicFactory:
    # Placeholder because otherwise linter screams
    pass


class ComponentModificationTests(TestCase):
    def test_change_component_to_hidden(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2_textfield1",
                        "hidden": False,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form_step=step2,
            component="step2_textfield1",
            json_logic_trigger={
                "==": {
                    {"var": "step1_textfield1"},
                    "hide step 2",
                }
            },
            actions=[
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1_textfield1": "hide step 2"},
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        configuration = evaluate_form_logic(submission_step_2, submission.data)

        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "step2_textfield1",
                    "hidden": True,
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_extract_value(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2_textfield1",
                        "hidden": False,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form_step=step2,
            component="step2_textfield1",
            json_logic_trigger={
                {"var": "step1_textfield1"},
            },
            actions=[
                {
                    "name": "Set extracted value",
                    "type": "value",
                    "value": "step1_textfield1",
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1_textfield1": "some value"},
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        configuration = evaluate_form_logic(submission_step_2, submission.data)

        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "step2_textfield1",
                    "hidden": False,
                    "value": "some value",
                }
            ]
        }
        self.assertEqual(configuration, expected)
