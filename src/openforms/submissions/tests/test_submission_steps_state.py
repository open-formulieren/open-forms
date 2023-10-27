"""
Test the derived properties on submissions and submission steps.

These properties are availability, completeness, current/not current etc. The depend
on which phase of the submission/total form the user is, and are serialized in the
API responses.
"""

from django.test import TestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from .factories import SubmissionFactory, SubmissionStepFactory


class SubmissionStepsStateTests(TestCase):
    def test_no_steps_at_all_submitted(self):
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(3, form=form)
        submission = SubmissionFactory.create(form=form)

        steps = submission.steps

        self.assertEqual(len(steps), 3)  # exactly three form steps
        self.assertFalse(any(step.pk for step in steps))
        # check the ordering
        self.assertEqual(steps[0].form_step, step1)
        self.assertEqual(steps[1].form_step, step2)
        self.assertEqual(steps[2].form_step, step3)
        # verify that none of them are completed
        self.assertTrue(all(not step.completed for step in steps))

    def test_steps_correct_order(self):
        form = FormFactory.create()
        step2 = FormStepFactory.create(form=form, order=2)
        step1 = FormStepFactory.create(form=form, order=1)
        submission = SubmissionFactory.create(form=form)

        steps = submission.steps

        self.assertEqual(steps[0].form_step, step1)
        self.assertEqual(steps[1].form_step, step2)

    def test_step_completed(self):
        form = FormFactory.create()
        step1, step2 = FormStepFactory.create_batch(2, form=form)
        submission = SubmissionFactory.create(form=form)

        with self.subTest(submissions="none"):
            steps = submission.steps

            self.assertFalse(steps[0].completed)
            self.assertFalse(steps[1].completed)

        with self.subTest(submissions="first step"):
            SubmissionStepFactory.create(
                form_step=step1, submission=submission, data={}
            )
            submission.refresh_from_db()

            steps = submission.steps

            self.assertTrue(steps[0].completed)
            self.assertFalse(steps[1].completed)

        with self.subTest(submissions="second and last step"):
            SubmissionStepFactory.create(
                form_step=step2, submission=submission, data={}
            )
            submission.refresh_from_db()

            steps = submission.steps

            self.assertTrue(steps[0].completed)
            self.assertTrue(steps[1].completed)

    def test_step_set_applicable(self):
        form = FormFactory.create()
        step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            form_step=step, submission=submission, data={}
        )

        self.assertIsNone(submission_step._is_applicable)
        self.assertTrue(submission_step.is_applicable)
        submission_step.is_applicable = False
        self.assertFalse(submission_step.is_applicable)
