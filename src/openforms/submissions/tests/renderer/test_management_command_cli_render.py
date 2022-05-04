"""
Integration test for a full render management command.
"""
from io import StringIO

from django.core.management import call_command
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
    # wysiwyg
    {
        "type": "content",
        "key": "wysiwyg",
        "html": "<p>WYSIWYG with <strong>markup</strong></p>",
        "input": False,
        "label": "WYSIWYG Content",
        "hidden": False,
    },
]


class CLIRendererIntegrationTests(TestCase):
    maxDiff = None

    def test_render_submission_in_cli_no_html(self):
        submission = SubmissionFactory.create(
            form__name="public name",
            form__internal_name="internal name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__name="Stap 1",
            form__formstep__form_definition__configuration={
                "components": FORMIO_CONFIGURATION_COMPONENTS
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "input1": "first input",
                "input2": "second input",
                "amount": 1234.56,
                "input4": "fourth input",
            },
        )
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "render_report",
            [submission.id],
            as_html=False,
            stdout=stdout,
            stderr=stderr,
        )

        stdout.seek(0)
        stderr.seek(0)
        self.assertEqual(stderr.read(), "")

        output = stdout.read()
        expected = f"""
Submission {submission.id} - public name
    Stap 1
        ---------------------------------  -------------------
        Input 1                            first input
        Currency                           1.234,56
        A container with visible children
        Input 4                            fourth input
        WYSIWYG Content                    WYSIWYG with markup
        ---------------------------------  -------------------
"""
        self.assertEqual(output, expected)

    def test_render_submission_in_cli_with_html(self):
        submission = SubmissionFactory.create(
            form__name="public name",
            form__internal_name="internal name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__name="Stap 1",
            form__formstep__form_definition__configuration={
                "components": FORMIO_CONFIGURATION_COMPONENTS
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "input1": "first input",
                "input2": "second input",
                "amount": 1234.56,
                "input4": "fourth input",
            },
        )
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "render_report",
            [submission.id],
            as_html=True,
            stdout=stdout,
            stderr=stderr,
        )

        stdout.seek(0)
        stderr.seek(0)
        self.assertEqual(stderr.read(), "")

        output = stdout.read()
        expected = f"""
Submission {submission.id} - public name
    Stap 1
        ---------------------------------  -------------------------------------------
        Input 1                            first input
        Currency                           1.234,56
        A container with visible children
        Input 4                            fourth input
        WYSIWYG Content                    <p>WYSIWYG with <strong>markup</strong></p>
        ---------------------------------  -------------------------------------------
"""
        self.assertEqual(output, expected)
