from base64 import b64decode
from pathlib import Path

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase

from requests import RequestException
from zgw_consumers.test.factories import ServiceFactory

from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import JSONDumpRegistration

VCR_TEST_FILES = Path(__file__).parent / "files"


class JSONDumpBackendTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = VCR_TEST_FILES

    def test_submission_with_json_dump_backend(self):
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

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["firstName", "file", "auth_bsn"],
        )
        json_plugin = JSONDumpRegistration("json_registration_plugin")
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

        res = json_plugin.register_submission(submission, json_form_options)
        res_json = res["api_response"].json()

        self.assertEqual(res_json, expected_response)

        with self.subTest("attachment content encoded"):
            decoded_content = b64decode(res_json["data"]["values"]["file"])
            self.assertEqual(decoded_content, b"This is example content.")

    def test_exception_raised_when_service_returns_unexpected_status_code(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textField"},
                {"key": "lastName", "type": "textfield"},
            ],
            completed=True,
            submitted_data={"firstName": "We Are", "lastName": "Checking"},
            bsn="123456789",
        )

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="fake_endpoint",
            form_variables=["firstName", "auth_bsn"],
        )
        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        with self.assertRaises(RequestException):
            json_plugin.register_submission(submission, json_form_options)

    def test_multiple_file_uploads(self):
        submission = SubmissionFactory.from_components(
            [{"key": "file", "type": "file", "multiple": True}],
            completed=True,
            submitted_data={
                "file": [
                    {
                        "url": "some://url",
                        "name": "file1.txt",
                        "type": "application/text",
                        "originalName": "file1.txt",
                    },
                    {
                        "url": "some://url",
                        "name": "file2.txt",
                        "type": "application/text",
                        "originalName": "file2.txt",
                    }
                ],
            },
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="file1.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="file2.txt",
            content_type="application/text",
            content__data=b"Content example is this.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["file"],
        )
        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        expected_values = {
            "file": {
                "file1.txt": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",  # This is example content.
                "file2.txt": "Q29udGVudCBleGFtcGxlIGlzIHRoaXMu",  # Content example is this.
            },
        }

        res = json_plugin.register_submission(submission, json_form_options)
        res_json = res["api_response"]

        self.assertEqual(res_json["data"]["values"], expected_values)

    def test_path_traversal_attack(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textField"},
                {"key": "lastName", "type": "textfield"},
            ],
            completed=True,
            submitted_data={
                "firstName": "We Are",
                "lastName": "Checking",
            },
            bsn="123456789",
        )

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            path="..",
            form_variables=["firstName", "file", "auth_bsn"],
        )
        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        for path in ("..", "../foo", "foo/..", "foo/../bar"):
            with self.subTest(path):
                json_form_options["path"] = path
                with self.assertRaises(SuspiciousOperation):
                    json_plugin.register_submission(submission, json_form_options)
