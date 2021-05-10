from django.test import TestCase

from ...forms.tests.factories import FormFactory, FormStepFactory
from .factories import SubmissionFactory, SubmissionStepFactory


class SubmissionStepAvailabilityTests(TestCase):
    def test_basic_merge(self):
        form = FormFactory()
        step_1 = FormStepFactory(form=form)
        step_2 = FormStepFactory(form=form)
        step_3 = FormStepFactory(form=form)
        submission = SubmissionFactory(form=form)
        SubmissionStepFactory(
            form_step=step_1, submission=submission, data={"foo": 1, "bar": 2}
        )
        SubmissionStepFactory(form_step=step_2, submission=submission, data={"bazz": 3})
        SubmissionStepFactory(form_step=step_3, submission=submission, data={"buzz": 4})

        actual = submission.get_merged_data()
        expected = {
            "foo": 1,
            "bar": 2,
            "bazz": 3,
            "buzz": 4,
        }
        self.assertEqual(actual, expected)
