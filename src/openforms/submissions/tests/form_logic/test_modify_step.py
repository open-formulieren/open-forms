from django.test import TestCase

from freezegun import freeze_time

from openforms.formio.service import FormioData
from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory


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

        evaluate_form_logic(submission, submission_step_2)

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
                    "form_step_uuid": f"{step2.uuid}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step_1 = SubmissionStepFactory.create(
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

        evaluate_form_logic(submission, submission_step_1)
        submission_state = submission.load_execution_state()
        updated_step_2 = submission_state.get_submission_step(
            form_step_uuid=str(step2.uuid)
        )

        self.assertFalse(updated_step_2.is_applicable)

    def test_step_applicable(self):
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
            is_applicable=False,
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
                    "form_step_uuid": f"{step2.uuid}",
                    "action": {
                        "name": "Step is applicable",
                        "type": "step-applicable",
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step_1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"age": 16},
        )
        # not saved in DB!
        submission_step_2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
        )

        self.assertTrue(submission_step_1.is_applicable)
        # _is_applicable = None by default -> should look at form_step.is_applicable:
        self.assertFalse(submission_step_2.is_applicable)

        evaluate_form_logic(submission, submission_step_1)
        submission_state = submission.load_execution_state()
        updated_step_2 = submission_state.get_submission_step(
            form_step_uuid=str(step2.uuid)
        )

        self.assertTrue(updated_step_2.is_applicable)

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

        evaluate_form_logic(submission, submission_step)

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
            evaluate_form_logic(submission, submission_step)

        self.assertFalse(submission_step.can_submit)

    def test_only_diff_data_returned(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                    },
                    {
                        "type": "textfield",
                        "key": "changingKey",
                    },
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
                    "variable": "changingKey",
                    "action": {
                        "name": "Set value",
                        "type": LogicActionTypes.variable,
                        "value": "changed",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=step
        )

        data = FormioData(
            {
                "name": "john",
                "changingKey": "original",
            }
        )

        evaluate_form_logic(submission, submission_step, data)

        self.assertEqual(
            submission_step.data,
            {"changingKey": "changed"},
        )

    def test_select_boxes_trigger(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "currentPets",
                        "values": [
                            {"label": "Cat", "value": "cat"},
                            {"label": "Dog", "value": "dog"},
                            {"label": "Fish", "value": "fish"},
                        ],
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "currentPets.cat"},
                    True,
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
            data={"currentPets": {"cat": True, "dog": False, "fish": False}},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission, submission_step)

        self.assertFalse(submission_step.can_submit)

    def test_select_boxes_trigger_with_dot_in_key_name(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "current.pets",
                        "values": [
                            {"label": "Cat", "value": "cat"},
                            {"label": "Dog", "value": "dog"},
                            {"label": "Fish", "value": "fish"},
                        ],
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "current.pets.cat"},
                    True,
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
            data={"current": {"pets": {"cat": True, "dog": False, "fish": False}}},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission, submission_step)

        self.assertFalse(submission_step.can_submit)

    def test_normal_component_trigger_with_dot_in_key_name(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [{"key": "normal.component", "type": "textfield"}]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "normal.component"},
                    "test-value",
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
            data={"normal": {"component": "test-value"}},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission, submission_step)

        self.assertFalse(submission_step.can_submit)

    def test_component_removed_from_definition(self):
        # Test for issue #1568
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={
                "name": "Jane",
                "surname": "Doe",
            },  # Data for component no longer in the definition
        )

        # This shouldn't raise an error
        evaluate_form_logic(submission, submission_step)

    def test_datetime_trigger(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "datetime",
                        "key": "startOfConstructionWorks",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            # Is the start datetime of the construction works more than 24h in the future?
            json_logic_trigger={
                ">": [
                    {"datetime": {"var": "startOfConstructionWorks"}},
                    {"+": [{"var": "now"}, {"rdelta": [0, 0, 0, 24]}]},
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
            data={"startOfConstructionWorks": "2023-01-18T16:00:00+01:00"},
        )

        self.assertTrue(submission_step.can_submit)

        with freeze_time(
            "2023-01-16T16:00:00+01:00"
        ):  # The start of construction is 48h in the future
            evaluate_form_logic(submission, submission_step)

        self.assertFalse(submission_step.can_submit)
