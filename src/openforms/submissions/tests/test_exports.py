from datetime import datetime
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils import timezone

import time_machine
from privates.test import temp_private_root

from openforms.formio.rendering.nodes import ComponentNode
from openforms.formio.tests.factories import SubmittedFileFactory
from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ..exports import create_submission_export
from ..models import Submission
from ..rendering.constants import RenderModes
from ..rendering.nodes import FormNode
from ..rendering.renderer import Renderer
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


class ExportTests(TestCase):
    def test_export_empty_queryset(self):
        dataset = create_submission_export(Submission.objects.none())

        self.assertEqual(len(dataset), 0)
        self.assertIsNone(dataset.headers)

    def test_export_keeps_value_for_duplicate_field(self):
        submission = SubmissionFactory.create()
        renderer = Renderer(submission, mode=RenderModes.export, as_html=False)
        nodes = [FormNode(renderer=renderer)]
        nodes.extend(
            ComponentNode(
                renderer=renderer,
                component={"type": "textfield", "key": "field"},
                step_data={"field": value},
            )
            for value in (None, "Test", None)
        )
        with patch(
            "openforms.submissions.exports.iter_submission_data_nodes",
            return_value=iter(nodes),
        ):
            dataset = create_submission_export(Submission.objects.all())

        self.assertEqual(dataset.headers, ["Formuliernaam", "Inzendingdatum", "field"])
        self.assertEqual(dataset.dict[0]["field"], "Test")

    @time_machine.travel("2022-05-09T13:00:00Z", tick=False)
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
                    "label": "input1",
                    "hidden": False,
                },
                {
                    "type": "textfield",
                    "key": "input2",
                    "label": "input2",
                    "hidden": True,
                    "clearOnHide": False,
                },
                {
                    "type": "fieldset",
                    "key": "fieldset1",
                    "label": "fieldset1",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input3",
                            "label": "input3",
                            "hidden": False,
                        },
                        {
                            "type": "textfield",
                            "key": "input4",
                            "label": "input4",
                            "hidden": True,
                            "clearOnHide": False,
                        },
                    ],
                },
                {
                    "type": "columns",
                    "key": "columns1",
                    "label": "columns1",
                    "hidden": True,
                    "columns": [
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "input5",
                                    "label": "input5",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "input6",
                                    "label": "input6",
                                    "hidden": True,
                                    "clearOnHide": False,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "content",
                    "key": "content",
                    "label": "content",
                    "html": "<p>Some wysigyg content</p>",
                },
            ],
            submitted_data={
                "input1": "Input 1",
                "input2": "",
                "input3": "Input 3",
                "input4": "",
                "input6": "",
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
                "",
                "Input 3",
                "",
                None,
                "",
            ),
        )

    @time_machine.travel("2022-05-09T13:00:00Z", tick=False)
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

    def test_export_with_user_defined_variable_not_present_in_all_submissions(self):
        form = FormFactory.create(generate_minimal_setup=True)
        submission_1, submission_2 = SubmissionFactory.create_batch(2, form=form)
        SubmissionValueVariableFactory.create(
            key="ud1",
            value={"nested": "value"},
            submission=submission_2,
            form_variable__user_defined=True,
        )

        dataset = create_submission_export(
            Submission.objects.filter(
                pk__in=[submission_1.pk, submission_2.pk]
            ).order_by("pk")
        )

        self.assertEqual(len(dataset), 2)
        self.assertIsNone(dataset.dict[0]["ud1"])
        self.assertEqual(dataset.dict[1]["ud1"], {"nested": "value"})

    @tag("gh-2117")
    @time_machine.travel("2022-05-09T13:00:00Z", tick=False)
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
                        "label": "input1",
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
                        "label": "input2",
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
    @time_machine.travel(None, tick=False)
    def test_submissions_of_forms_with_translation_enabled_have_language_codes(self):
        SubmissionFactory.create(
            form__translation_enabled=True,
            language_code="en",
        )
        export = create_submission_export(Submission.objects.all())

        self.assertIn(("Taalcode", "en"), zip(export.headers, export[0], strict=False))

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
                        "groupLabel": "item",
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
                        "file": {"type": []},
                        "filePattern": "",
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
