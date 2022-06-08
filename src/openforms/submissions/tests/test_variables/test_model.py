from django.db import IntegrityError
from django.test import TestCase

from ..factories import SubmissionValueVariableFactory


class SubmissionValueVariableModelTests(TestCase):
    def test_unique_together_submission_key(self):
        variable1 = SubmissionValueVariableFactory.create(key="var1")

        with self.assertRaises(IntegrityError):
            SubmissionValueVariableFactory.create(
                submission=variable1.submission, key="var1"
            )

    def test_unique_together_submission_form_variable(self):
        variable1 = SubmissionValueVariableFactory.create()

        with self.assertRaises(IntegrityError):
            SubmissionValueVariableFactory.create(
                submission=variable1.submission, form_variable=variable1.form_variable
            )

    def test_can_create_instances(self):
        variable1 = SubmissionValueVariableFactory.create()
        variable2 = SubmissionValueVariableFactory.create()
