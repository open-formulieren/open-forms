from django.test import TestCase

from openforms.appointments.contrib.qmatic.tests.factories import ServiceFactory
from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..plugin import JSONRegistration


class JSONBackendTests(TestCase):
    # VCR_TEST_FILES = VCR_TEST_FILES

    def test_submission_with_json_backend(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textField"},
                {"key": "lastName", "type": "textfield"},
                {"key": "file", "type": "file"},
            ],
            completed=True,
            submitted_data={
                "firstName": "We Are",
                "lastName": "Checking",
                "file": [
                    {
                        "url": "some://url",
                        "name": "my-foo.bin",
                        "type": "application/foo",
                        "originalName": "my-foo.bin",
                    }
                ],
            },
            bsn="123456789",
        )

        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        json_form_options = dict(
            service=ServiceFactory(api_root="http://example.com/api/v2"),
            relative_api_endpoint="",
            form_variables=["firstName", "lastName", "file", "auth_bsn"],
        )
        email_submission = JSONRegistration("json_plugin")

        set_submission_reference(submission)

        data_to_be_sent = email_submission.register_submission(submission, json_form_options)

        expected_data_to_be_sent = {
            "values": {
                "firstName": "We Are",
                "lastName": "Checking",
                "file": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",
                "auth_bsn": "123456789",
            }
        }
        self.assertEqual(data_to_be_sent, expected_data_to_be_sent)
