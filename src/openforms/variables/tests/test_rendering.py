from django.test import TestCase

from openforms.forms.constants import FormVariableSources
from openforms.submissions.exports import iter_submission_data_nodes
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionValueVariableFactory,
)


class VariablesNodeTests(TestCase):
    def test_user_defined_vars_in_export(self):
        config = {
            "components": [
                {
                    "type": "textfield",
                    "key": "input1",
                    "label": "Input 1",
                    "hidden": False,
                },
            ]
        }
        data = {
            "input1": "aaaaa",
        }

        submission = SubmissionFactory.from_components(
            components_list=config["components"], submitted_data=data
        )
        SubmissionValueVariableFactory.create(
            key="ud1",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
        )

        nodelist = list(iter_submission_data_nodes(submission))
        labels = [node.label for node in nodelist]

        self.assertEqual(len(labels), 2)
        self.assertEqual(
            labels,
            ["input1", "ud1"],
        )

    def test_rendering_user_defined_vars(self):
        submission = SubmissionFactory.create(form__name="Test email confirmation")
        SubmissionValueVariableFactory.create(
            key="ud1",
            value="Some data 1",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=True,
            form_variable__show_in_pdf=True,
            form_variable__show_in_summary=True,
        )
        SubmissionValueVariableFactory.create(
            key="ud2",
            value="Some data 2",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=False,
            form_variable__show_in_pdf=False,
            form_variable__show_in_summary=False,
        )

        for mode in [RenderModes.export, RenderModes.cli, RenderModes.registration]:
            with self.subTest(action=f"Mode: {mode}"):
                renderer = Renderer(submission=submission, mode=mode, as_html=False)

                nodes = [node for node in renderer]
                rendered = [node.render() for node in nodes]

                self.assertEqual(len(nodes), 4)
                self.assertEqual(
                    rendered,
                    [
                        "Test email confirmation",
                        "Variables",
                        "ud1: Some data 1",
                        "ud2: Some data 2",
                    ],
                )

        for mode in [RenderModes.pdf, RenderModes.confirmation_email]:
            with self.subTest(action=f"Mode: {mode}"):
                renderer = Renderer(submission=submission, mode=mode, as_html=False)

                nodes = [node for node in renderer]
                rendered = [node.render() for node in nodes]

                self.assertEqual(len(nodes), 3)
                self.assertEqual(
                    rendered,
                    ["Test email confirmation", "Variables", "ud1: Some data 1"],
                )
