from unittest import expectedFailure

from django.test import TestCase

from openforms.formio.service import FormioData
from openforms.submissions.tests.factories import SubmissionFactory

from ...form_logic import evaluate_form_logic


class ConditionalLogicTests(TestCase):
    @expectedFailure
    def test_clear_existing(self):
        """Ensure that a hidden component with existing submission data is cleared.

        This fails right now because we deliberately only check the conditional and not
        the hidden property. When all clearOnHide processing is done, this *should* not
        fail anymore.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfieldVisible",
                    "label": "Textfield visible",
                    "hidden": False,
                    "clearOnHide": True,
                },
                {
                    "type": "textfield",
                    "key": "textfieldHidden",
                    "label": "Textfield hidden",
                    "hidden": True,
                    "clearOnHide": True,
                },
            ],
            submitted_data={
                "textfieldVisible": "keep me",
                "textfieldHidden": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(data, {"textfieldVisible": "keep me", "textfieldHidden": ""})
        self.assertEqual(step.unsaved_data, {})

    def test_clear_initially_visible(self):
        """
        Ensure that the data of an initially visible component is cleared when
        conditionally hidden. Also ensures that the default is to clear the value when
        clearOnHide is not specified.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfieldVisible",
                    "label": "Textfield visible",
                    "hidden": False,
                },
                {
                    "type": "textfield",
                    "key": "textfieldConditionallyHidden",
                    "label": "Textfield to hide",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "textfieldVisible",
                        "eq": "hide",
                    },
                    "clearOnHide": True,
                },
                {
                    "type": "textfield",
                    "key": "textfieldConditionallyHidden2",
                    "label": "Textfield to hide 2",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "textfieldVisible",
                        "eq": "hide",
                    },
                },
            ],
            submitted_data={
                "textfieldVisible": "hide",
                "textfieldConditionallyHidden": "clear me",
                "textfieldConditionallyHidden2": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfieldVisible": "hide",
                "textfieldConditionallyHidden": "",
                "textfieldConditionallyHidden2": "",
            },
        )
        self.assertEqual(step.unsaved_data, {})

    def test_parent_component_hidden(self):
        """
        Ensure that the data of an initially visible nested component is cleared when
        the layout parent is conditionally hidden.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfieldVisible",
                    "label": "Textfield visible",
                    "hidden": False,
                },
                {
                    "type": "fieldset",
                    "key": "fieldset",
                    "label": "Fieldset",
                    "hidden": False,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "nestedTextfield",
                            "label": "Nested textfield",
                            "clearOnHide": True,
                        },
                        {
                            "type": "textfield",
                            "key": "nestedTextfield2",
                            "label": "Nested textfield 2",
                            "clearOnHide": False,
                        },
                    ],
                    "conditional": {
                        "show": False,
                        "when": "textfieldVisible",
                        "eq": "hide fieldset",
                    },
                },
            ],
            submitted_data={
                "textfieldVisible": "hide fieldset",
                "nestedTextfield": "clear me",
                "nestedTextfield2": "keep me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfieldVisible": "hide fieldset",
                "nestedTextfield": "",
                "nestedTextfield2": "keep me",
            },
        )
        self.assertEqual(step.unsaved_data, {})

    def test_hidden_component_in_layout(self):
        """
        Ensure that the data of an initially visible nested component is cleared when
        it is conditionally hidden.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfieldVisible",
                    "label": "Textfield visible",
                    "hidden": False,
                },
                {
                    "type": "fieldset",
                    "key": "fieldset",
                    "label": "Fieldset",
                    "hidden": False,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "nestedTextfield",
                            "label": "Nested textfield",
                            "clearOnHide": True,
                            "conditional": {
                                "show": False,
                                "when": "textfieldVisible",
                                "eq": "hide nested",
                            },
                        },
                    ],
                },
            ],
            submitted_data={
                "textfieldVisible": "hide nested",
                "nestedTextfield": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {"textfieldVisible": "hide nested", "nestedTextfield": ""},
        )
        self.assertEqual(step.unsaved_data, {})

    def test_editgrid_are_independent(self):
        """
        Ensure that items inside an editgrid are independent from each other, and nested
        components clear their value when hidden.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "editgrid",
                    "key": "editgrid",
                    "label": "Edit grid",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "trigger",
                            "label": "Trigger",
                        },
                        {
                            "type": "fieldset",
                            "key": "fieldset",
                            "label": "Fieldset",
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "follower",
                                    "label": "Follower",
                                    "clearOnHide": True,
                                },
                            ],
                            "conditional": {
                                "show": False,
                                "when": "editgrid.trigger",
                                "eq": "hide",
                            },
                        },
                    ],
                }
            ],
            submitted_data={
                "editgrid": [
                    {"trigger": "show", "follower": "keep me"},
                    {"trigger": "hide", "follower": "clear me"},
                ]
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "editgrid": [
                    {"trigger": "show", "follower": "keep me"},
                    {"trigger": "hide", "follower": ""},
                ]
            },
        )
        self.assertEqual(step.unsaved_data, {})

    def test_dependent_fields(self):
        """
        Ensure that component dependencies resolve irrespective of where they are in the
        component tree
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfield1",
                    "label": "Textfield 1",
                    "clearOnHide": True,
                },
                {
                    "type": "textfield",
                    "key": "textfield2",
                    "label": "Textfield 2",
                    "clearOnHide": True,
                    "conditional": {
                        "show": True,
                        "when": "textfield3",
                        "eq": "visible",
                    },
                },
                {
                    "type": "textfield",
                    "key": "textfield3",
                    "label": "Textfield 3",
                    "clearOnHide": True,
                    "conditional": {
                        "show": False,
                        "when": "textfield1",
                        "eq": "hidden",
                    },
                },
                {
                    "type": "textfield",
                    "key": "textfield4",
                    "label": "Textfield 4",
                    "clearOnHide": True,
                    "conditional": {
                        "show": True,
                        "when": "textfield3",
                        "eq": "visible",
                    },
                },
                {
                    "type": "textfield",
                    "key": "textfield5",
                    "label": "Textfield 5",
                    "defaultValue": "default",
                    "conditional": {
                        "show": True,
                        "when": "textfield2",
                        "eq": "",
                    },
                },
            ],
            submitted_data={
                "textfield1": "",
                "textfield2": "visible",
                "textfield3": "visible",
                "textfield4": "visible",
                "textfield5": "",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(
            submission,
            step,
            FormioData({"textfield1": "hidden"}),
            use_new_behaviour=True,
        )

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfield1": "hidden",
                "textfield2": "",
                "textfield3": "",
                "textfield4": "",
                "textfield5": "",
            },
        )
        self.assertEqual(step.unsaved_data, {})

    def test_component_multiple(self):
        """
        Ensure that we perform a membership test instead of a direct comparison
        between values when a component is configured as multiple.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "textfieldVisible",
                    "label": "Textfield visible",
                    "multiple": True,
                    "hidden": False,
                },
                {
                    "type": "textfield",
                    "key": "textfieldConditionallyHidden",
                    "label": "Textfield to hide",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "textfieldVisible",
                        "eq": "a",
                    },
                    "clearOnHide": True,
                },
            ],
            submitted_data={
                "textfieldVisible": ["a", "b", "c"],
                "textfieldConditionallyHidden": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step, use_new_behaviour=True)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfieldVisible": ["a", "b", "c"],
                "textfieldConditionallyHidden": "",
            },
        )
        self.assertEqual(step.unsaved_data, {})
