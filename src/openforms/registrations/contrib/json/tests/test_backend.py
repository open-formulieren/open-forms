from django.test import TestCase

from requests import RequestException
from zgw_consumers.test.factories import ServiceFactory

from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..plugin import JSONRegistration

VCR_TEST_FILES = Path(__file__).parent / "files"


class JSONBackendTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = VCR_TEST_FILES

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

        expected_response = {
            # Note that `lastName` is not included here as it wasn't specified in the form_variables
            "data": {
                "values": {
                    "auth_bsn": "123456789",
                    "file": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",  # Content of the attachment encoded using base64
                    "firstName": "We Are",
                },
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "static_var_1": {"type": "string", "pattern": "^cool_pattern$"},
                        "form_var_1": {"type": "string"},
                        "form_var_2": {"type": "string"},
                        "attachment": {"type": "string", "contentEncoding": "base64"},
                    },
                    "required": ["static_var_1", "form_var_1", "form_var_2"],
                    "additionalProperties": False,
                },
            },
            "message": "Data received",
        }
        self.assertEqual(data_to_be_sent, expected_data_to_be_sent)
