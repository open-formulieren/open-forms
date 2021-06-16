from django.test import TestCase

from openforms.forms.tests.factories import FormDefinitionFactory, FormStepFactory

from .factories import SubmissionFactory, SubmissionStepFactory


class TestSubmission(TestCase):
    def test_get_merged_data(self):
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"key1": "value1", "key2": "value2"},
            form_step=FormStepFactory.create(),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"key2": "value-a", "key3": "value-b"},
            form_step=FormStepFactory.create(),
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=FormStepFactory.create()
        )

        self.assertEqual(
            submission.get_merged_data(),
            {"key1": "value1", "key2": "value-a", "key3": "value-b"},
        )

    def test_get_merged_data_with_component_types(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "key", "type": "textfield"},
                    {"key": "key2", "type": "textarea"},
                    {"key": "key3", "type": "checkbox"},
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"key": "this is some text", "key2": "this is text in a text area"},
            form_step=FormStepFactory.create(form_definition=form_definition),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"key2": "this is other text in a text area", "key3": True},
            form_step=FormStepFactory.create(form_definition=form_definition),
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=FormStepFactory.create()
        )

        self.assertEqual(
            submission.get_merged_data_with_component_type(),
            {
                "key": {"type": "textfield", "value": "this is some text"},
                "key2": {
                    "type": "textarea",
                    "value": "this is other text in a text area",
                },
                "key3": {"type": "checkbox", "value": True},
            },
        )
