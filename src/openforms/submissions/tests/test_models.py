from collections import OrderedDict

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

    def test_get_ordered_data_with_component_type(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "key", "type": "textfield", "label": "Label"},
                    {"key": "key2", "type": "textarea", "label": "Label2"},
                    {"key": "key3", "type": "checkbox", "label": "Label3"},
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
            data={"key3": True, "key2": "this is text in a text area"},
            form_step=FormStepFactory.create(
                form=submission.form, form_definition=form_definition
            ),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "key5": "this is some inner text",
                "key": "this is some text",
                "key2": "this is other text in a text area",
            },
            form_step=FormStepFactory.create(
                form=submission.form, form_definition=form_definition
            ),
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=FormStepFactory.create(form=submission.form),
        )
        actual = submission.get_ordered_data_with_component_type()
        expected = OrderedDict(
            [
                (
                    "key",
                    {
                        "type": "textfield",
                        "value": "this is some text",
                        "label": "Label",
                    },
                ),
                (
                    "key2",
                    {
                        "type": "textarea",
                        "value": "this is other text in a text area",
                        "label": "Label2",
                    },
                ),
                ("key3", {"type": "checkbox", "value": True, "label": "Label3"}),
                (
                    "key5",
                    {
                        "type": "textfield",
                        "value": "this is some inner text",
                        "label": "key5",
                    },
                ),
            ]
        )
        self.assertEqual(actual, expected)

    def test_get_printable_data_with_selectboxes(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "testSelectBoxes",
                        "type": "selectboxes",
                        "label": "My Boxes",
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
            form_step=FormStepFactory.create(
                form=submission.form, form_definition=form_definition
            ),
        )

        ordered = submission.get_ordered_data_with_component_type()
        self.assertEqual(
            ordered,
            {
                "testSelectBoxes": {
                    "type": "selectboxes",
                    "label": "My Boxes",
                    "value": {"test1": True, "test2": True, "test3": False},
                }
            },
        )
        printable_data = submission.get_printable_data()

        self.assertEqual(
            printable_data["My Boxes"],
            "test1, test2",
        )

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

        submission = SubmissionFactory.create(
            form=form, bsn="999990676", kvk="69599084"
        )
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

        submission.refresh_from_db()
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
        self.assertTrue(submission._is_cleaned)
        self.assertEqual(submission.bsn, "")
        self.assertEqual(submission.kvk, "")

    def test_get_merged_appointment_data(self):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                    {
                        "key": "phoneNumber",
                        "appointments": {"phoneNumber": True},
                        "label": "Phone Number",
                    },
                    {
                        "key": "randomAttribute",
                        "appointments": {"birthDate": False},
                        "label": "Random attribute",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "location": {"identifier": "1", "name": "Amsterdam"},
                "time": "2021-08-25T17:00:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
                "phoneNumber": "+31 20 753 05 23",
                "randomAttribute": "This is some random stuff",
            },
            form_step=form_step_2,
        )

        self.assertEqual(
            submission.get_merged_appointment_data(),
            {
                "productIDAndName": {
                    "label": "Product",
                    "value": {"identifier": "79", "name": "Paspoort"},
                },
                "locationIDAndName": {
                    "label": "Location",
                    "value": {"identifier": "1", "name": "Amsterdam"},
                },
                "appStartTime": {"label": "Time", "value": "2021-08-25T17:00:00"},
                "clientLastName": {"label": "Last Name", "value": "Maykin"},
                "clientDateOfBirth": {"label": "Date of Birth", "value": "1990-08-01"},
                "clientPhoneNumber": {
                    "label": "Phone Number",
                    "value": "+31 20 753 05 23",
                },
            },
        )

    def test_can_submit_returns_false_when_form_can_not_be_submitted(self):
        submission_step = SubmissionStepFactory.create(
            submission__form__can_submit=False
        )
        self.assertFalse(submission_step.can_submit)
