from django.test import TestCase

import requests_mock

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.registrations.contrib.stuff_dms.plugin import create_zaak_plugin
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


@requests_mock.Mocker()
class StufDMSBackendTests(TestCase):
    def setUp(self):
        self.form = FormFactory.create()
        self.fd = FormDefinitionFactory.create()
        self.fs = FormStepFactory.create(form=self.form, form_definition=self.fd)

    def test_backend(self, m):
        form_options = dict()

        data = {
            "voornaam": "Foo",
        }
        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )

        result = create_zaak_plugin(submission, form_options)
        self.assertEqual(
            result,
            {
                "TODO": True,
            },
        )
