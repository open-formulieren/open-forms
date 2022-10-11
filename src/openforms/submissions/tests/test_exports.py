from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.variables.constants import FormVariableSources

from ..exports import create_submission_export
from ..models import Submission
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


class ExportTests(TestCase):
    @freeze_time("2022-05-09T13:00:00Z")
    def test_complex_formio_configuration(self):
        """
        Assert that complex formio configurations are exported correctly.

        The hidden/visible state may be the result of static or dynamic (logic)
        configuration.

        All form keys should always be present, even if they are hidden.
        """
        SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "input1",
                    "hidden": False,
                },
                {
                    "type": "textfield",
                    "key": "input2",
                    "hidden": True,
                },
                {
                    "type": "fieldset",
                    "key": "fieldset1",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input3",
                            "hidden": False,
                        },
                        {
                            "type": "textfield",
                            "key": "input4",
                            "hidden": True,
                        },
                    ],
                },
                {
                    "type": "columns",
                    "key": "columns1",
                    "hidden": True,
                    "columns": [
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "input5",
                                    "hidden": False,
                                },
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "input6",
                                    "hidden": True,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "content",
                    "key": "content",
                    "html": "<p>Some wysigyg content</p>",
                },
            ],
            submitted_data={
                "input1": "Input 1",
                "input3": "Input 3",
            },
            form__name="Export test",
            completed=True,
            completed_on=timezone.now(),
        )

        dataset = create_submission_export(Submission.objects.all())

        self.assertEqual(
            dataset.headers,
            [
                "Formuliernaam",
                "Inzendingdatum",
                "input1",
                "input2",
                "input3",
                "input4",
                "input5",
                "input6",
            ],
        )
        self.assertEqual(
            dataset[0],
            (
                "Export test",
                datetime(2022, 5, 9, 15, 0, 0),
                "Input 1",
                None,
                "Input 3",
                None,
                None,
                None,
            ),
        )

    @freeze_time("2022-05-09T13:00:00Z")
    def test_user_defined_variables_in_export(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "input1",
                    "hidden": False,
                }
            ],
            submitted_data={
                "input1": "Input 1",
            },
            form__name="Export test",
            completed=True,
            completed_on=timezone.now(),
        )
        SubmissionValueVariableFactory.create(
            key="ud1",
            value="Some value",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__form=submission.form,
        )

        dataset = create_submission_export(Submission.objects.all())

        self.assertEqual(
            dataset.headers,
            [
                "Formuliernaam",
                "Inzendingdatum",
                "input1",
                "ud1",
            ],
        )
        self.assertEqual(
            dataset[0],
            (
                "Export test",
                datetime(2022, 5, 9, 15, 0, 0),
                "Input 1",
                "Some value",
            ),
        )

    @freeze_time("2022-05-09T13:00:00Z")
    def test_submission_export_with_mixed_fields_and_forms(self):
        # Github issue #2117
        form = FormFactory.create(name="Export form 1")
        form_step_1 = FormStepFactory(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "input1",
                    }
                ]
            },
        )
        form_step_2 = FormStepFactory(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "input2",
                    }
                ]
            },
        )
        # first submission with two steps
        submission_1 = SubmissionFactory.create(
            form=form, completed=True, completed_on=timezone.now()
        )
        SubmissionStepFactory.create(
            submission=submission_1,
            form_step=form_step_1,
            data={"input1": "sub1.input1"},
        )
        SubmissionStepFactory.create(
            submission=submission_1,
            form_step=form_step_2,
            data={"input2": "sub1.input2"},
        )

        # second submission with one step
        submission_2 = SubmissionFactory.create(
            form=form, completed=True, completed_on=timezone.now()
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=form_step_1,
            data={"input1": "sub2.input1"},
        )

        # third whole different form with different fields
        SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "different1",
                }
            ],
            submitted_data={"different1": "sub3.different1"},
            form__name="Export form 2",
            completed=True,
            completed_on=timezone.now(),
        )

        dataset = create_submission_export(Submission.objects.all())

        self.assertEqual(
            dataset.headers,
            [
                "Formuliernaam",
                "Inzendingdatum",
                "input1",
                "input2",
                "different1",
            ],
        )

        self.assertEqual(
            dataset[0],
            (
                "Export form 1",
                datetime(2022, 5, 9, 15, 0, 0),
                "sub1.input1",
                "sub1.input2",
                "",
            ),
        )
        self.assertEqual(
            dataset[1],
            (
                "Export form 1",
                datetime(2022, 5, 9, 15, 0, 0),
                "sub2.input1",
                "",
                "",
            ),
        )
        self.assertEqual(
            dataset[2],
            (
                "Export form 2",
                datetime(2022, 5, 9, 15, 0, 0),
                "",
                "",
                "sub3.different1",
            ),
        )
