from django.test import TestCase, override_settings

from openforms.submissions.exports import iter_submission_data_nodes
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


@override_settings(LANGUAGE_CODE="nl")
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
            key="ud1", submission=submission, form_variable__user_defined=True
        )

        nodelist = list(iter_submission_data_nodes(submission))
        labels = [node.label for node in nodelist]

        self.assertEqual(len(labels), 2)
        self.assertEqual(
            labels,
            ["input1", "ud1"],
        )

    def test_rendering_user_defined_vars(self):
        submission = SubmissionFactory.create(form__name="Form rendering")
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__name="Form step rendering",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "someField",
                        "label": "Some field",
                        "type": "textfield",
                        "showInEmail": True,
                        "showInPDF": True,
                    },
                ],
            },
            data={"someField": "Some test data"},
        )
        SubmissionValueVariableFactory.create(
            key="ud1",
            value="Some data 1",
            submission=submission,
            form_variable__user_defined=True,
            form_variable__name="User defined var 1",
        )
        SubmissionValueVariableFactory.create(
            key="ud2",
            value="Some data 2",
            submission=submission,
            form_variable__user_defined=True,
            form_variable__name="User defined var 2",
        )

        with self.subTest(action="Mode: export"):
            renderer = Renderer(
                submission=submission, mode=RenderModes.export, as_html=False
            )

            nodes = [node for node in renderer]
            rendered = [node.render() for node in nodes]

            self.assertEqual(
                rendered,
                [
                    "Form rendering",
                    "",
                    "someField: Some test data",
                    "",
                    "ud1: Some data 1",
                    "ud2: Some data 2",
                ],
            )

        with self.subTest(action="Mode: registration"):
            renderer = Renderer(
                submission=submission, mode=RenderModes.registration, as_html=False
            )

            nodes = [node for node in renderer]
            rendered = [node.render() for node in nodes]

            self.assertEqual(
                rendered,
                [
                    "Form rendering",
                    "Form step rendering",
                    "Some field: Some test data",
                    "Variabelen",
                    "User defined var 1: Some data 1",
                    "User defined var 2: Some data 2",
                ],
            )

        with self.subTest(action="Mode: cli"):
            renderer = Renderer(
                submission=submission, mode=RenderModes.cli, as_html=False
            )

            nodes = [node for node in renderer]
            rendered = [node.render() for node in nodes]

            self.assertEqual(
                rendered,
                [
                    "Form rendering",
                    "Form step rendering",
                    "Some field: Some test data",
                    "Variabelen",
                    "User defined var 1: Some data 1",
                    "User defined var 2: Some data 2",
                ],
            )

        for mode in [RenderModes.pdf, RenderModes.confirmation_email]:
            with self.subTest(action=f"Mode: {mode}"):
                renderer = Renderer(submission=submission, mode=mode, as_html=False)

                nodes = [node for node in renderer]
                rendered = [node.render() for node in nodes]

                self.assertEqual(
                    rendered,
                    [
                        "Form rendering",
                        "Form step rendering",
                        "Some field: Some test data",
                    ],
                )
