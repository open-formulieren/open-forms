from django.test import TestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

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
                    {
                        "key": "key4",
                        "type": "fieldset",
                        "components": [{"key": "key5", "type": "textfield"}],
                    },
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
            data={
                "key2": "this is other text in a text area",
                "key3": True,
                "key5": "this is some inner text",
            },
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
                "key5": {"type": "textfield", "value": "this is some inner text"},
            },
        )

    def test_get_printable_data_with_selectboxes(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "testSelectBoxes",
                        "type": "selectboxes",
                        "values": [
                            {"values": "test1", "label": "test1", "shortcut": ""},
                            {"values": "test2", "label": "test2", "shortcut": ""},
                            {"values": "test3", "label": "test3", "shortcut": ""},
                        ],
                    },
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"testSelectBoxes": {"test1": True, "test2": True, "test3": False}},
            form_step=FormStepFactory.create(form_definition=form_definition),
        )

        printable_data = submission.get_printable_data()

        self.assertEqual(
            printable_data["testSelectBoxes"],
            "test1, test2",
        )

    def test_submission_has_sensitive_information(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive", "isSensitiveData": False},
                ],
            }
        )
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "textFieldSensitive": "this is sensitive",
                "textFieldNotSensitive": "this is not sensitive",
            },
            form_step=form_step,
        )

        self.assertTrue(submission.has_sensitive_information)

    def test_submission_remove_sensitive_data(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive", "isSensitiveData": False},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive2", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive2", "isSensitiveData": False},
                ],
            }
        )
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={
                "textFieldSensitive": "this is sensitive",
                "textFieldNotSensitive": "this is not sensitive",
            },
            form_step=form_step,
        )
        submission_step_2 = SubmissionStepFactory.create(
            submission=submission,
            data={
                "textFieldSensitive2": "this is sensitive",
                "textFieldNotSensitive2": "this is not sensitive",
            },
            form_step=form_step_2,
        )

        submission.remove_sensitive_data()

        submission_step.refresh_from_db()
        submission_step_2.refresh_from_db()

        self.assertEqual(submission_step.data["textFieldSensitive"], "")
        self.assertEqual(
            submission_step.data["textFieldNotSensitive"], "this is not sensitive"
        )
        self.assertEqual(submission_step_2.data["textFieldSensitive2"], "")
        self.assertEqual(
            submission_step_2.data["textFieldNotSensitive2"], "this is not sensitive"
        )
