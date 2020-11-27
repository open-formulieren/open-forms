"""
Test the derived properties on submissions and submission steps.

These properties are availability, completeness, current/not current etc. The depend
on which phase of the submission/total form the user is, and are serialized in the
API responses.
"""

from django.test import TestCase

from openforms.core.tests.factories import FormFactory, FormStepFactory

from .factories import Submission, SubmissionFactory, SubmissionStepFactory


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

    def test_current_step_moving(self):
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(3, form=form)
        submission = SubmissionFactory.create(form=form)

        with self.subTest(submissions="none"):
            steps = submission.steps

            self.assertTrue(steps[0].current)
            self.assertFalse(steps[1].current)
            self.assertFalse(steps[2].current)

        with self.subTest(submissions="first step"):
            SubmissionStepFactory.create(
                form_step=step1, submission=submission, data={}
            )

            steps = submission.steps

            self.assertFalse(steps[0].current)
            self.assertTrue(steps[1].current)
            self.assertFalse(steps[2].current)

        with self.subTest(submissions="second step"):
            SubmissionStepFactory.create(
                form_step=step2, submission=submission, data={}
            )

            steps = submission.steps

            self.assertFalse(steps[0].current)
            self.assertFalse(steps[1].current)
            self.assertTrue(steps[2].current)

        with self.subTest(submissions="third and last step"):
            SubmissionStepFactory.create(
                form_step=step3, submission=submission, data={}
            )

            steps = submission.steps

            self.assertFalse(steps[0].current)
            self.assertFalse(steps[1].current)
            self.assertFalse(steps[2].current)

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

            steps = submission.steps

            self.assertTrue(steps[0].completed)
            self.assertFalse(steps[1].completed)

        with self.subTest(submissions="second and last step"):
            SubmissionStepFactory.create(
                form_step=step2, submission=submission, data={}
            )

            steps = submission.steps

            self.assertTrue(steps[0].completed)
            self.assertTrue(steps[1].completed)
