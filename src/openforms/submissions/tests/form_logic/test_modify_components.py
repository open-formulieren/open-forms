import unittest

from django.test import TestCase, tag

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory


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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

    @tag("gh-1871", "gh-2340", "gh-2409")
    def test_hiding_component_empties_its_data(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "component1"},
                    "trigger value",
                ]
            },
            actions=[
                {
                    "component": "component2",
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
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "component1": "trigger value",
                "component2": "Some data to be deleted",
            },
        )

        configuration = evaluate_form_logic(submission, submission_step)

        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "component1",
                    "hidden": False,
                    "clearOnHide": True,
                },
                {
                    "type": "textfield",
                    "key": "component2",
                    "hidden": True,
                    "clearOnHide": True,
                },
            ]
        }
        self.assertEqual(configuration, expected)
        self.assertEqual("", submission_step.data["component2"])

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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
                    "variable": "step2_textfield1",
                    "action": {
                        "name": "Set extracted value",
                        "type": LogicActionTypes.variable,
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

        configuration = evaluate_form_logic(submission, submission_step_2)

        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "step2_textfield1",
                    "hidden": False,
                }
            ]
        }
        self.assertEqual(configuration, expected)
        self.assertEqual({"step2_textfield1": "some value"}, submission_step_2.data)

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

        configuration = evaluate_form_logic(submission, submission_step_2)

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

    def test_change_component_with_nested_components(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "Cat1",
                        "type": "fieldset",
                        "label": "Cat 1",
                        "legend": "Cat 1",
                        "hidden": False,
                        "components": [
                            {
                                "key": "CatBirthDate",
                                "type": "date",
                                "format": "dd-MM-yyyy",
                                "hidden": False,
                            },
                            {
                                "key": "addAnotherCat",
                                "type": "radio",
                                "hidden": False,
                                "values": [
                                    {"label": "Yes", "value": "yes"},
                                    {"label": "No", "value": "no"},
                                ],
                            },
                        ],
                    },
                    {
                        "key": "Cat2",
                        "type": "fieldset",
                        "label": "Cat 2",
                        "legend": "Cat 2",
                        "hidden": False,
                        "components": [
                            {
                                "key": "CatBirthDate2",
                                "type": "date",
                                "format": "dd-MM-yyyy",
                                "hidden": False,
                            }
                        ],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!=": [{"var": "addAnotherCat"}, "yes"]},
            actions=[
                {
                    "formStep": None,
                    "component": "Cat2",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={},
        )

        configuration = evaluate_form_logic(submission, submission_step)

        self.assertTrue(configuration["components"][1]["hidden"])

    def test_change_component_in_another_step_to_hidden(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield",
                    }
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2_textfield",
                        "hidden": False,
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield"},
                    "hide step2_textfield",
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
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1_textfield": "hide step2_textfield"},
        )

        configuration = evaluate_form_logic(submission, submission_step1)

        # Nothing changed in the current step, because the action in the rule references a component in another step
        expected = {
            "components": [
                {
                    "type": "textfield",
                    "key": "step1_textfield",
                }
            ]
        }
        self.assertEqual(configuration, expected)

    def test_component_visible_in_frontend(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "yes", "value": "yes"},
                            {"label": "no", "value": "no"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "textField",
                        "hidden": True,
                        "conditional": {"eq": "yes", "show": True, "when": "radio"},
                        "clearOnHide": True,
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"radio": "yes", "textField": "Some data that must not be cleared!"},
        )

        evaluate_form_logic(submission, submission_step)

        self.assertEqual(
            "Some data that must not be cleared!", submission_step.data["textField"]
        )

    @tag("gh-5520")
    @unittest.expectedFailure
    def test_component_visible_with_date(self):
        """
        Assert that the textfield is not cleared, as the conditional causes it to be
        visible. This currently fails because the value is not converted to a date
        object, whereas the submitted data for the date field is. Comparing a plain
        string with a date object will always fail.
        """
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "date",
                        "type": "date",
                    },
                    {
                        "type": "textfield",
                        "key": "textField",
                        "hidden": True,
                        "conditional": {
                            "eq": "2025-01-01",
                            "show": True,
                            "when": "date",
                        },
                        "clearOnHide": True,
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "date": "2025-01-01",
                "textField": "Some data that must not be cleared!",
            },
        )

        evaluate_form_logic(submission, submission_step)

        self.assertEqual(
            "Some data that must not be cleared!", submission_step.data["textField"]
        )

    @tag("gh-1183")
    def test_component_incomplete_frontend_logic(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textFieldA",
                        "hidden": True,
                        "conditional": {
                            "eq": "",
                            "show": "",
                            "when": None,
                        },  # show is "" instead of None
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "textFieldB",
                        "hidden": True,
                        "conditional": {
                            "eq": "yes",
                            "show": True,
                            "when": None,
                        },  # Partially filled rule
                        "clearOnHide": True,
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
        )

        # Does not raise exception
        evaluate_form_logic(submission, submission_step)

    @tag("gh-2781")
    def test_hiding_nested_field(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "nested.component",
                        "type": "textfield",
                        "clearOnHide": True,
                    },
                    {
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "radio"},
                    "a",
                ]
            },
            actions=[
                {
                    "component": "nested.component",
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
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"radio": "a", "nested": {"component": "test"}},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission, submission_step)

        self.assertEqual(submission_step.data["nested"]["component"], "")

    @tag("gh-2838")
    def test_hidden_select_component(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "hidden": True,
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "clearOnHide": True,
                        "defaultValue": {"a": False, "b": False},
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={},
        )

        self.assertTrue(submission_step.can_submit)

        evaluate_form_logic(submission, submission_step)

        self.assertNotIn("selectboxes", submission_step.data)

    @tag("gh-3744")
    def test_postcode_component_made_optional(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "nicePostcode",
                        "validate": {
                            "custom": "",
                            "unique": False,
                            "pattern": "^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
                            "plugins": [],
                            "multiple": False,
                            "required": True,
                            "maxLength": "",
                            "minLength": "",
                            "customMessage": "Invalid Postcode",
                            "customPrivate": False,
                            "strictDateValidation": False,
                        },
                    }
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "component": "nicePostcode",
                    "action": {
                        "name": "Make not required",
                        "type": "property",
                        "property": {
                            "type": "object",
                            "value": "validate.required",
                        },
                        "state": False,
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.build(
            submission=submission,
            form_step=step,
        )

        configuration = evaluate_form_logic(submission, submission_step)

        expected = {
            "components": [
                {
                    "type": "postcode",
                    "key": "nicePostcode",
                    "validate": {
                        "custom": "",
                        "unique": False,
                        "pattern": "^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
                        "plugins": [],
                        "multiple": False,
                        "required": False,  # Changed
                        "maxLength": "",
                        "minLength": "",
                        "customMessage": "Invalid Postcode",
                        "customPrivate": False,
                        "strictDateValidation": False,
                    },
                }
            ]
        }

        self.assertEqual(configuration, expected)
