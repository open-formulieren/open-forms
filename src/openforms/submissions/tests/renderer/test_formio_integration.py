"""
Test the vendor-agnostic renderer interface with FormIO components.
"""

from django.test import TestCase

from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

FORMIO_CONFIGURATION_COMPONENTS = [
    # visible component, leaf node
    {
        "type": "textfield",
        "key": "input1",
        "label": "Input 1",
        "hidden": False,
    },
    # hidden component, leaf node
    {
        "type": "textfield",
        "key": "input2",
        "label": "Input 2",
        "hidden": True,
    },
    {
        "type": "currency",
        "key": "amount",
        "label": "Currency",
        "hidden": False,
    },
    # container: visible fieldset with visible children
    {
        "type": "fieldset",
        "label": "A container with visible children",
        "hidden": False,
        "components": [
            {
                "type": "textfield",
                "key": "input3",
                "label": "Input 3",
                "hidden": True,
            },
            {
                "type": "textfield",
                "key": "input4",
                "label": "Input 4",
                "hidden": False,
            },
        ],
    },
]


class SubmissionRendererIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        submission = SubmissionFactory.create(
            form__name="public name",
            form__internal_name="internal name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__name="Stap 1",
            form__formstep__form_definition__configuration={
                "components": FORMIO_CONFIGURATION_COMPONENTS
            },
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "input1": "first input",
                "input2": "second input",
                "amount": 1234.56,
                "input4": "fourth input",
            },
        )

        # expose test data to test methods
        cls.submission = submission
        cls.step = step

    def test_all_nodes_returned_in_correct_order(self):
        renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

        nodelist = list(renderer)

        # form node, submission step node, then formio component nodes
        self.assertEqual(len(nodelist), 1 + 1 + 4)
        rendered = [node.render() for node in nodelist]

        expected = [
            "public name",
            "Stap 1",
            "Input 1: first input",
            "Currency: 1.234,56",
            "A container with visible children",
            "Input 4: fourth input",
        ]
        self.assertEqual(rendered, expected)
