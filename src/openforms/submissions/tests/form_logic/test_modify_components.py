from django.test import TestCase

from freezegun import freeze_time

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory
from .factories import FormLogicFactory


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
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 2",
                ]
            },
            actions=[
                {
                    "component": "step2_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
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

    def test_change_component_to_required(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
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
                        "key": "surname",
                        "validate": {"required": False},
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "name"},
                    "john",
                ]
            },
            actions=[
                {
                    "component": "surname",
                    "action": {
                        "name": "Make required",
                        "type": "property",
                        "property": {
                            "type": "object",
                            "value": "validate",
                        },
                        "state": {"required": True},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"name": "john"},
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
                    "key": "surname",
                    "validate": {"required": True},
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_change_component_to_hidden_if_text_contains(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "fooBarBaz",
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
                        "key": "test",
                        "hidden": True,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "in": [
                    {"var": "fooBarBaz"},
                    "foobarbaz",
                ]
            },
            actions=[
                {
                    "component": "test",
                    "action": {
                        "name": "Make element visible",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"fooBarBaz": "foo"},
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
                    "key": "test",
                    "hidden": False,
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_change_component_to_hidden_if_array_contains(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "email",
                        "key": "userEmail",
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
                        "key": "test",
                        "hidden": True,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "in": [
                    {"var": "userEmail"},
                    ["test1@example.com", "test2@example.com"],
                ]
            },
            actions=[
                {
                    "component": "test",
                    "action": {
                        "name": "Make element visible",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"userEmail": "test1@example.com"},
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
                    "key": "test",
                    "hidden": False,
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_dont_change_component_to_hidden_if_text_does_not_contain(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "fooBarBaz",
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
                        "key": "test",
                        "hidden": True,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "in": [
                    {"var": "fooBarBaz"},
                    "foobarbaz",
                ]
            },
            actions=[
                {
                    "component": "test",
                    "action": {
                        "name": "Make element visible",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"fooBarBaz": "hello"},
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
                    "key": "test",
                    "hidden": True,
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_dont_change_component_to_hidden_if_array_does_not_contain(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "email",
                        "key": "userEmail",
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
                        "key": "test",
                        "hidden": True,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "in": [
                    {"var": "userEmail"},
                    ["test1@example.com", "test2@example.com"],
                ]
            },
            actions=[
                {
                    "component": "test",
                    "action": {
                        "name": "Make element visible",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"userEmail": "test3@example.com"},
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
                    "key": "test",
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
            form=form,
            json_logic_trigger={"==": [1, 1]},
            actions=[
                {
                    "component": "step2_textfield1",
                    "action": {
                        "name": "Set extracted value",
                        "type": "value",
                        "value": {"var": "step1_textfield1"},
                    },
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

    def test_evaluate_logic_with_empty_data(self):
        """
        When the SDK first loads a form, it does an evaluation of the logic with an empty dict of data.
        In subsequent evaluations of the logic, the dict with the data may still not contain all the values,
        since they haven't been filled in yet.
        """
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
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
                        "key": "surname",
                        "validate": {"required": False},
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "name"},
                    "john",
                ]
            },
            actions=[
                {
                    "component": "surname",
                    "action": {
                        "name": "Make required",
                        "type": "property",
                        "property": {
                            "type": "json",
                            "value": "validate",
                        },
                        "state": {"required": True},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={},  # Empty data!
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        configuration = evaluate_form_logic(submission_step_2, submission.data)

        # Expect configuration unchanged
        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "surname",
                    "validate": {"required": False},
                }
            ]
        }
        self.assertEqual(configuration, expected)


class StepModificationTests(TestCase):
    def test_next_button_disabled(self):
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
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "disable next button",
                ]
            },
            actions=[
                {
                    "component": "step2_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "disable-next",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1_textfield1": "disable next button"},
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        self.assertTrue(submission_step_2.can_submit)

        evaluate_form_logic(submission_step_2, submission.data)

        self.assertFalse(submission_step_2.can_submit)

    def test_step_not_applicable(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
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
                        "key": "driverId",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "<": [
                    {"var": "age"},
                    18,
                ]
            },
            actions=[
                {
                    "component": "driverId",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"age": 16},
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        self.assertTrue(submission_step_2.is_applicable)

        evaluate_form_logic(submission_step_2, submission.data)

        self.assertFalse(submission_step_2.is_applicable)

    def test_date_trigger(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "<": [
                    {"date": {"var": "dateOfBirth"}},
                    {"date": "2021-01-01"},
                ]
            },
            actions=[
                {
                    "action": {
                        "name": "Disable next",
                        "type": "disable-next",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"dateOfBirth": "2020-01-01"},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission_step, submission.data)

        self.assertFalse(submission_step.can_submit)

    def test_date_of_birth_trigger(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"-": [{"today": []}, {"rdelta": [18]}]},
                ]
            },
            actions=[
                {
                    "action": {
                        "name": "Disable next",
                        "type": "disable-next",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"dateOfBirth": "2003-01-01"},
        )

        self.assertTrue(submission_step.can_submit)

        with freeze_time("2020-01-01"):
            evaluate_form_logic(submission_step, submission.data)

        self.assertFalse(submission_step.can_submit)
