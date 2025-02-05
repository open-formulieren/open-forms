from django.test import TestCase

from openforms.forms.tests.factories import FormVersionFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..registration_variables import register


def _get_variable(key: str, **kwargs):
    return register[key].get_static_variable(**kwargs)


class FormVersionTests(TestCase):
    def test_without_submission(self):
        variable = _get_variable("form_version")

        self.assertEqual(variable.initial_value, "")

    def test_with_submission(self):
        submission = SubmissionFactory.create()

        FormVersionFactory.create(form=submission.form, description="Version 1")
        FormVersionFactory.create(form=submission.form, description="Version 2")

        variable = _get_variable("form_version", submission=submission)

        self.assertEqual(variable.initial_value, "Version 2")
