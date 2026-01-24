from datetime import UTC, date, datetime, time

from django.test import TestCase, override_settings, tag

from openforms.forms.models import FormDefinition, FormVersion
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.models import Submission, SubmissionStep

from ..rendering import Renderer, RenderModes
from .factories import SubmissionFactory, SubmissionStepFactory


@tag("gh-2135")
@override_settings(LANGUAGE_CODE="nl")
class SubmissionStepDeletedRegressionTests(TestCase):
    def test_submission_step_not_lost_on_formstep_delete(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1",
                        "label": "step1",
                    },
                    {
                        "type": "date",
                        "key": "someDate",
                        "label": "someDate",
                    },
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "groupLabel": "item",
                        "components": [
                            {"key": "date", "type": "date", "label": "Date"},
                            {"key": "time", "type": "time", "label": "Time"},
                            {
                                "key": "datetime",
                                "type": "datetime",
                                "label": "Datetime",
                            },
                        ],
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2",
                        "label": "step2",
                    },
                ]
            },
        )
        submission = SubmissionFactory.create(form=form, completed=True)
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "step1": "stippenlift",
                "someDate": "2022-11-03",
                "editgrid": [
                    {
                        "date": "2000-01-01",
                        "time": "12:34:56",
                        "datetime": "2000-01-01T12:34:56Z",
                    }
                ],
            },
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"step2": "ik ben een alien"},
        )
        with self.subTest("check initial data setup"):
            self.assertEqual(
                submission.data,
                {
                    "step1": "stippenlift",
                    "step2": "ik ben een alien",
                    "someDate": date(2022, 11, 3),
                    "editgrid": [
                        {
                            "date": date(2000, 1, 1),
                            "time": time(12, 34, 56),
                            "datetime": datetime(2000, 1, 1, 12, 34, 56, tzinfo=UTC),
                        }
                    ],
                },
            )
            renderer = Renderer(
                submission=submission, mode=RenderModes.pdf, as_html=False
            )
            rendered = [node.render() for node in renderer]
            # Check that type info is used for display
            self.assertIn("someDate: 3 november 2022", rendered)
            self.assertIn("        Date: 1 januari 2000", rendered)
            self.assertIn("        Time: 12:34", rendered)
            self.assertIn("        Datetime: 1 januari 2000 12:34", rendered)

        # delete a form step
        step1.delete()

        # reload submission as fresh data object so we don't have any cached states
        submission = Submission.objects.get(pk=submission.pk)
        self.assertEqual(
            submission.data,
            {
                "step1": "stippenlift",
                "step2": "ik ben een alien",
                "someDate": date(2022, 11, 3),
                "editgrid": [
                    {
                        "date": date(2000, 1, 1),
                        "time": time(12, 34, 56),
                        "datetime": datetime(2000, 1, 1, 12, 34, 56, tzinfo=UTC),
                    }
                ],
            },
        )
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step1.pk).exists())
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step2.pk).exists())
        renderer = Renderer(submission=submission, mode=RenderModes.pdf, as_html=False)
        rendered = [node.render() for node in renderer]
        # Check that type info is used for display
        self.assertIn("someDate: 3 november 2022", rendered)
        self.assertIn("        Date: 1 januari 2000", rendered)
        self.assertIn("        Time: 12:34", rendered)
        self.assertIn("        Datetime: 1 januari 2000 12:34", rendered)

    def test_form_definition_also_deleted(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1",
                        "label": "step1",
                    },
                    {
                        "type": "date",
                        "key": "someDate",
                        "label": "someDate",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2",
                        "label": "step2",
                    },
                ]
            },
        )
        submission = SubmissionFactory.create(form=form, completed=True)
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1": "stippenlift", "someDate": "2022-11-03"},
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"step2": "ik ben een alien"},
        )

        # delete a form step
        step1.delete()
        # assert that the form definition was deleted too, because it was not re-usable
        self.assertIsNone(step1.form_definition.pk)
        self.assertEqual(FormDefinition.objects.count(), 1)

        # reload submission as fresh data object so we don't have any cached states
        submission = Submission.objects.get(pk=submission.pk)
        self.assertEqual(
            submission.data,
            {
                "step1": "stippenlift",
                "step2": "ik ben een alien",
                "someDate": date(2022, 11, 3),
            },
        )
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step1.pk).exists())
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step2.pk).exists())
        renderer = Renderer(submission=submission, mode=RenderModes.pdf, as_html=False)
        rendered = [node.render() for node in renderer]
        self.assertIn("step1: stippenlift", rendered)
        self.assertIn("step2: ik ben een alien", rendered)
        # check that type info is used for display
        self.assertIn("someDate: 3 november 2022", rendered)

    def test_restore_old_form_version(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1",
                        "label": "step1",
                    },
                    {
                        "type": "date",
                        "key": "someDate",
                        "label": "someDate",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2",
                        "label": "step2",
                    },
                ]
            },
        )
        version = FormVersion.objects.create_for(form=form)
        submission = SubmissionFactory.create(form=form, completed=True)
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1": "stippenlift", "someDate": "2022-11-03"},
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"step2": "ik ben een alien"},
        )

        # trigger form step deletion via form version restoration
        form.restore_old_version(version.uuid)

        # reload submission as fresh data object so we don't have any cached states
        submission = Submission.objects.get(pk=submission.pk)
        self.assertEqual(
            submission.data,
            {
                "step1": "stippenlift",
                "step2": "ik ben een alien",
                "someDate": date(2022, 11, 3),
            },
        )
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step1.pk).exists())
        self.assertTrue(SubmissionStep.objects.filter(pk=submission_step2.pk).exists())
        renderer = Renderer(submission=submission, mode=RenderModes.pdf, as_html=False)
        rendered = [node.render() for node in renderer]
        self.assertIn("step1: stippenlift", rendered)
        self.assertIn("step2: ik ben een alien", rendered)
        # check that type info is used for display
        self.assertIn("someDate: 3 november 2022", rendered)
