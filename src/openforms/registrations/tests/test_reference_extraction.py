"""
Test the submission reference extraction behaviour, independent from the plugin.
"""
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..service import NoSubmissionReference, extract_submission_reference


class GenericReferenceExtractionTests(TestCase):
    def test_submission_not_completed(self):
        submission = SubmissionFactory.build(completed=False)

        with self.assertRaises(NoSubmissionReference):
            extract_submission_reference(submission)

    def test_submission_registration_not_completed(self):
        submissions = [
            SubmissionFactory.build(registration_failed=True),
            SubmissionFactory.build(registration_pending=True),
            SubmissionFactory.build(registration_in_progress=True),
        ]

        for submission in submissions:
            with self.subTest(registration_status=submission.registration_status):
                with self.assertRaises(NoSubmissionReference):
                    extract_submission_reference(submission)

    def test_submission_registered_but_no_registration_result(self):
        submission = SubmissionFactory.build(
            registration_success=True, registration_result={}
        )

        with self.assertRaises(NoSubmissionReference):
            extract_submission_reference(submission)
