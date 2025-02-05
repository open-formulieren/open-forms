"""
Integration test for a full render management command.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from ..factories import SubmissionFactory, SubmissionValueVariableFactory

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
        "key": "fieldsetVisibleChildren",
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


@override_settings(LANGUAGE_CODE="nl")
class CLIRendererIntegrationTests(TestCase):
    maxDiff = None

    def test_render_submission_in_cli_no_html(self):
        submission = SubmissionFactory.from_components(
            components_list=FORMIO_CONFIGURATION_COMPONENTS,
            submitted_data={
                "input1": "first input",
                "input2": "second input",
                "amount": 1234.56,
                "input4": "fourth input",
            },
            form__name="public name",
            form__internal_name="internal name",
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

        form_definition = submission.steps[0].form_step.form_definition
        form_definition.name = "Stap 1"
        form_definition.save()

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
                                           WYSIWYG with markup
        ---------------------------------  -------------------
    Variabelen
        ------------------  -----------
        User defined var 1  Some data 1
        User defined var 2  Some data 2
        ------------------  -----------
"""
        self.assertEqual(output, expected)

    def test_render_submission_in_cli_with_html(self):
        submission = SubmissionFactory.from_components(
            components_list=FORMIO_CONFIGURATION_COMPONENTS,
            submitted_data={
                "input1": "first input",
                "input2": "second input",
                "amount": 1234.56,
                "input4": "fourth input",
            },
            form__name="public name",
            form__internal_name="internal name",
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

        form_definition = submission.steps[0].form_step.form_definition
        form_definition.name = "Stap 1"
        form_definition.save()

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
                                           <p>WYSIWYG with <strong>markup</strong></p>
        ---------------------------------  -------------------------------------------
    Variabelen
        ------------------  -----------
        User defined var 1  Some data 1
        User defined var 2  Some data 2
        ------------------  -----------
"""
        self.assertEqual(output, expected)
