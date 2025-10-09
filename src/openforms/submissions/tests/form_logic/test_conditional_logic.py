from django.test import TestCase, tag

from openforms.formio.service import FormioData
from openforms.submissions.tests.factories import SubmissionFactory

from ...form_logic import evaluate_form_logic


class ConditionalLogicTests(TestCase):
    def test_clear_existing(self):
        """Ensure that a hidden component with existing submission data is cleared."""
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

        evaluate_form_logic(submission, step)

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
                    "type": "file",
                    "key": "file",
                    "hidden": False,
                    "conditional": {
                        "eq": False,
                        "show": "hide",
                        "when": "textfieldVisible",
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
                "file": [{"clear": "me"}],
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfieldVisible": "hide",
                "textfieldConditionallyHidden": "",
                "textfieldConditionallyHidden2": "",
                "file": [],
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

        evaluate_form_logic(submission, step)

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
                    "type": "columns",
                    "key": "columns",
                    "label": "Columns",
                    "hidden": False,
                    "columns": [
                        {
                            "size": 6,
                            "mobileSize": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "nestedTextfieldConditionallyHidden",
                                    "label": "Nested textfield",
                                    "clearOnHide": True,
                                    "conditional": {
                                        "show": False,
                                        "when": "textfieldVisible",
                                        "eq": "hide nested",
                                    },
                                }
                            ],
                        },
                        {
                            "size": 6,
                            "mobileSize": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "nestedTextfield",
                                    "label": "Nested textfield",
                                    "clearOnHide": True,
                                }
                            ],
                        },
                    ],
                },
            ],
            submitted_data={
                "textfieldVisible": "hide nested",
                "nestedTextfieldConditionallyHidden": "clear me",
                "nestedTextfield": "keep me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "textfieldVisible": "hide nested",
                "nestedTextfieldConditionallyHidden": "",
                "nestedTextfield": "keep me",
            },
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

        evaluate_form_logic(submission, step)

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

    def test_nested_editgrid(self):
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
                            "type": "editgrid",
                            "key": "editgrid2",
                            "label": "editgrid2",
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "follower",
                                    "label": "Follower",
                                    "clearOnHide": True,
                                    "conditional": {
                                        "show": False,
                                        "when": "editgrid.trigger",
                                        "eq": "hide",
                                    },
                                },
                            ],
                        },
                    ],
                }
            ],
            submitted_data={
                "editgrid": [
                    {
                        "trigger": "show",
                        "editgrid2": [
                            {"follower": "keep me"},
                            {"follower": "keep me as well"},
                        ],
                    },
                    {
                        "trigger": "hide",
                        "editgrid2": [
                            {"follower": "clear me"},
                            {"follower": "you better clear me too"},
                        ],
                    },
                ]
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "editgrid": [
                    {
                        "trigger": "show",
                        "editgrid2": [
                            {"follower": "keep me"},
                            {"follower": "keep me as well"},
                        ],
                    },
                    {
                        "trigger": "hide",
                        "editgrid2": [{"follower": ""}, {"follower": ""}],
                    },
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

        evaluate_form_logic(submission, step, FormioData({"textfield1": "hidden"}))

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

        evaluate_form_logic(submission, step)

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

    def test_selectboxes(self):
        """
        Ensure that we check whether the compare value inside a selectboxes dictionary
        is set to True.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "label": "selectboxes visible",
                    "values": [
                        {"value": "a", "label": "a"},
                        {"value": "b", "label": "b"},
                        {"value": "c", "label": "c"},
                    ],
                },
                {
                    "type": "textfield",
                    "key": "textfield1",
                    "label": "Textfield 1",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "selectboxes",
                        "eq": "a",
                    },
                    "clearOnHide": True,
                },
                {
                    "type": "textfield",
                    "key": "textfield2",
                    "label": "Textfield 2",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "selectboxes",
                        "eq": "b",
                    },
                    "clearOnHide": True,
                },
            ],
            submitted_data={
                "selectboxes": {"a": False, "b": True, "c": False},
                "textfield1": "keep me",
                "textfield2": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False)
        self.assertEqual(
            data,
            {
                "selectboxes": {"a": False, "b": True, "c": False},
                "textfield1": "keep me",
                "textfield2": "",
            },
        )
        self.assertEqual(step.unsaved_data, {})

    @tag("gh-2056")
    def test_file_component_hidden_by_frontend_has_correct_empty_value(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "yes", "value": "yes"},
                        {"label": "no", "value": "no"},
                    ],
                },
                {
                    "type": "file",
                    "key": "file",
                    "hidden": False,
                    "conditional": {"eq": "yes", "show": True, "when": "radio"},
                    "clearOnHide": True,
                },
            ]
        )

        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False, include_unsaved=True)
        self.assertEqual(data["file"], [])
        self.assertEqual(step.unsaved_data, {})

    def test_non_registered_components(self):
        """
        Ensure conditional logic evaluation does not crash when non-registered
        components are used
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "6ea64a10-7f04-470b-b3e1-2a247771ad74",
                    "key": "nonRegisteredComponentTrigger",
                    "label": "Non-registered trigger",
                },
                {
                    "type": "6ea64a10-7f04-470b-b3e1-2a247771ad74",
                    "key": "nonRegisteredComponentFollower",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "nonRegisteredComponentTrigger",
                        "eq": "hide",
                    },
                    "clearOnHide": True,
                },
            ],
            submitted_data={
                "nonRegisteredComponentTrigger": "hide",
                "nonRegisteredComponentFollower": "clear me",
            },
        )
        step = submission.submissionstep_set.first()

        evaluate_form_logic(submission, step)

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_static_variables=False, include_unsaved=True)
        self.assertEqual(
            data,
            {
                "nonRegisteredComponentTrigger": "hide",
                "nonRegisteredComponentFollower": "",
            },
        )
        self.assertEqual(step.unsaved_data, {})
