from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..utils import store_auth_details, store_registrator_details


class UtilsTests(TestCase):
    def test_store_auth_details(self):
        submission = SubmissionFactory.create()

        with self.assertRaises(ValueError):
            store_auth_details(
                submission,
                {"plugin": "digid", "attribute": "WRONG", "value": "some-value"},
            )

    def test_store_registrator_details(self):
        submission = SubmissionFactory.create()

        with self.assertRaises(ValueError):
            store_registrator_details(
                submission,
                {"plugin": "digid", "attribute": "WRONG", "value": "some-value"},
            )
