"""
Test the derived properties on submissions and submission steps.

These properties are availability, completeness, current/not current etc. The depend
on which phase of the submission/total form the user is, and are serialized in the
API responses.
"""

from django.test import TestCase

from openforms.forms.constants import AvailabilityOptions
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


class SubmissionNextStepTests(TestCase):
    def test_next_step_all_required_sequential_submission(self):
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(3, form=form)
        submission = SubmissionFactory.create(form=form)

        with self.subTest(submissions="none"):
            next_step = submission.get_next_step().form_step

            self.assertEqual(next_step, step1)

        with self.subTest(submissions="first step"):
            SubmissionStepFactory.create(
                form_step=step1, submission=submission, data={}
            )
            submission.refresh_from_db()

            next_step = submission.get_next_step().form_step

            self.assertEqual(next_step, step2)

        with self.subTest(submissions="second step"):
            SubmissionStepFactory.create(
                form_step=step2, submission=submission, data={}
            )
            submission.refresh_from_db()

            next_step = submission.get_next_step().form_step

            self.assertEqual(next_step, step3)

        with self.subTest(submissions="third and last step"):
            SubmissionStepFactory.create(
                form_step=step3, submission=submission, data={}
            )
            submission.refresh_from_db()

            next_step = submission.get_next_step()

            self.assertEqual(next_step, None)

    def test_next_step_non_sequential_submission(self):
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(3, form=form)
        submission = SubmissionFactory.create(form=form)

        with self.subTest(submissions="none"):
            next_step = submission.get_next_step().form_step

            self.assertEqual(next_step, step1)

        with self.subTest(submissions="second step"):
            SubmissionStepFactory.create(
                form_step=step2, submission=submission, data={}
            )
            submission.refresh_from_db()

            next_step = submission.get_next_step().form_step

            self.assertEqual(next_step, step3)

    def test_next_step_based_on_last_modification(self):
        """
        Test that step 2 is the next step if step 1 is the last touched step.
        """
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(3, form=form)
        submission = SubmissionFactory.create(form=form)
        # first submit step 3, then 1 -> the next step is 2 and not None
        SubmissionStepFactory.create(form_step=step3, submission=submission, data={})
        SubmissionStepFactory.create(form_step=step1, submission=submission, data={})

        next_step = submission.get_next_step().form_step

        self.assertEqual(next_step, step2)


class SubmissionStepAvailabilityTests(TestCase):
    def test_always_available(self):
        form = FormFactory.create()
        step1, step2, step3 = FormStepFactory.create_batch(
            3, form=form, availability_strategy=AvailabilityOptions.always
        )
        submission = SubmissionFactory.create(form=form)

        for step in submission.steps:
            with self.subTest(step=step):
                self.assertTrue(step.available)

    def test_conditional_availability(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(form=form)
        step2, step3 = FormStepFactory.create_batch(
            2, form=form, availability_strategy=AvailabilityOptions.after_previous_step
        )
        submission = SubmissionFactory.create(form=form)

        with self.subTest(submissions="none"):
            steps = submission.steps

            self.assertTrue(steps[0].available)
            self.assertFalse(steps[1].available)
            self.assertFalse(steps[2].available)

        with self.subTest(submissions="step1"):
            SubmissionStepFactory.create(
                form_step=step1, submission=submission, data={}
            )
            submission.refresh_from_db()

            steps = submission.steps

            self.assertTrue(steps[0].available)
            self.assertTrue(steps[1].available)
            self.assertFalse(steps[2].available)
