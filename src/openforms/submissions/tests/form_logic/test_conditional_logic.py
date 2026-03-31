from django.test import TestCase, tag

from openforms.formio.service import FormioData
from openforms.submissions.tests.factories import SubmissionFactory

from ...form_logic import evaluate_form_logic


class ConditionalLogicTests(TestCase):
    @tag("gh-6140")
    def test_fieldset_inside_editgrid(self):
        """
        Ensure that items inside a fieldset inside an editgrid are properly handled.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "editgrid",
                    "key": "editgrid",
                    "label": "Edit grid",
                    "components": [
                        {
                            "type": "fieldset",
                            "key": "fieldset",
                            "label": "Fieldset",
                            "components": [
                                {
                                    "type": "selectboxes",
                                    "key": "trigger",
                                    "label": "Trigger",
                                    "values": [
                                        {"label": "foo", "value": "foo"},
                                        {"label": "bar", "value": "bar"},
                                    ],
                                },
                                {
                                    "type": "textfield",
                                    "key": "follower",
                                    "label": "Follower",
                                    "clearOnHide": True,
                                    "conditional": {
                                        "show": True,
                                        "when": "editgrid.trigger",
                                        "eq": "foo",
                                    },
                                },
                            ],
                        },
                    ],
                }
            ],
            form__new_renderer_enabled=True,
        )
        step = submission.submissionstep_set.get()

        evaluate_form_logic(
            submission,
            step,
            FormioData(
                {
                    "editgrid": [
                        {"trigger": {"foo": True, "bar": False}, "follower": "keep me"},
                        {
                            "trigger": {"foo": False, "bar": False},
                            "follower": "clear me",
                        },
                    ]
                }
            ),
        )

        state = submission.variables_state
        data = state.get_data(include_static_variables=False, include_unsaved=True)
        self.assertEqual(
            data,
            {
                "editgrid": [
                    {"trigger": {"foo": True, "bar": False}, "follower": "keep me"},
                    {"trigger": {"foo": False, "bar": False}, "follower": ""},
                ]
            },
        )
        self.assertEqual(step.unsaved_data, {})
