"""
Test the submission reference extraction behaviour, independent from the plugin.
"""
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..service import NoSubmissionReference, extract_submission_reference


class GenericReferenceExtractionTests(TestCase):
    def test_submission_not_completed(self):
        raise NotImplementedError

    def test_submission_registration_not_completed(self):
        raise NotImplementedError

    def test_submission_registered_but_no_registration_result(self):
        raise NotImplementedError
