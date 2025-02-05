from datetime import datetime

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.formio.tests.factories import SubmittedFileFactory
from openforms.forms.tests.factories import FormFactory, FormStepFactory

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
            form_variable__user_defined=True,
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

    @tag("gh-2117")
    @freeze_time("2022-05-09T13:00:00Z")
    def test_submission_export_with_mixed_fields(self):
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

        # second submission with just one step
        submission_2 = SubmissionFactory.create(
            form=form, completed=True, completed_on=timezone.now()
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=form_step_1,
            data={"input1": "sub2.input1"},
        )

        dataset = create_submission_export(Submission.objects.order_by("-pk"))

        self.assertEqual(
            dataset.headers,
            [
                "Formuliernaam",
                "Inzendingdatum",
                "input1",
                "input2",
            ],
        )

        self.assertEqual(
            dataset[0],
            (
                "Export form 1",
                datetime(2022, 5, 9, 15, 0, 0),
                "sub2.input1",
                None,
            ),
        )
        self.assertEqual(
            dataset[1],
            (
                "Export form 1",
                datetime(2022, 5, 9, 15, 0, 0),
                "sub1.input1",
                "sub1.input2",
            ),
        )

    @tag("gh-2389")
    @freeze_time()
    def test_submissions_of_forms_with_translation_enabled_have_language_codes(self):
        SubmissionFactory.create(
            form__translation_enabled=True,
            language_code="en",
        )
        export = create_submission_export(Submission.objects.all())

        self.assertIn(("Taalcode", "en"), zip(export.headers, export[0]))

    @tag("gh-3629")
    def test_different_number_of_items_in_repeating_groups(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "repeatingGroup",
                        "label": "Repeating group",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "fullName",
                                "label": "Full name",
                            }
                        ],
                    }
                ]
            },
        )
        submission_1, submission_2 = SubmissionFactory.create_batch(
            2, form=form, completed=True, completed_on=timezone.now()
        )
        SubmissionStepFactory.create(
            submission=submission_1,
            form_step=form.formstep_set.get(),
            # no records at all, ensure first submission has less items than second
            data={"repeatingGroup": []},
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=form.formstep_set.get(),
            # 1 record, more than the first submission
            data={"repeatingGroup": [{"fullName": "Herman Brood"}]},
        )

        dataset = create_submission_export(Submission.objects.order_by("pk"))

        self.assertEqual(len(dataset), 2)
        self.assertEqual(len(dataset.headers), 3)
        self.assertEqual(dataset.headers[2], "repeatingGroup")
        self.assertIsNotNone(dataset[0][2])
        self.assertIsNotNone(dataset[1][2])

    @tag("gh-3629")
    @temp_private_root()
    def test_form_with_file_uploads(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "attachments",
                        "label": "Attachments",
                        "multiple": True,
                    }
                ]
            },
        )
        submission_1, submission_2 = SubmissionFactory.create_batch(
            2, form=form, completed=True, completed_on=timezone.now()
        )
        SubmissionStepFactory.create(
            submission=submission_1,
            form_step=form.formstep_set.get(),
            data={
                "attachments": [
                    SubmittedFileFactory.create(
                        temporary_upload__submission=submission_1
                    )
                ]
            },
        )
        files_2 = SubmittedFileFactory.create_batch(
            2, temporary_upload__submission=submission_2
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=form.formstep_set.get(),
            # 1 record, more than the first submission
            data={"attachments": files_2},
        )

        dataset = create_submission_export(Submission.objects.order_by("pk"))

        self.assertEqual(len(dataset), 2)

    @tag("gh-3629")
    def test_submission_missing_submission_step(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "fullName",
                        "label": "Full name",
                    }
                ]
            },
        )
        submission_1, submission_2 = SubmissionFactory.create_batch(
            2, form=form, completed=True, completed_on=timezone.now()
        )
        assert not submission_1.submissionstep_set.exists()
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=form.formstep_set.get(),
            data={"fullName": "Arie Kabaalstra"},
        )

        dataset = create_submission_export(Submission.objects.order_by("pk"))

        self.assertEqual(len(dataset), 2)
        self.assertEqual(len(dataset[0]), 3)
        self.assertEqual(len(dataset[1]), 3)
