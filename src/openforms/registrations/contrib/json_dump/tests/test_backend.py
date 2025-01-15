from base64 import b64decode
from pathlib import Path

from django.test import TestCase

from glom import glom
from requests import RequestException
from zgw_consumers.test.factories import ServiceFactory

from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    FormVariableFactory,
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

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
        res_json = res["api_response"]

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
                    },
                ],
            },
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="file1.txt",
            original_name="file1.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="file2.txt",
            original_name="file2.txt",
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

        res = json_plugin.register_submission(submission, json_form_options)
        res_json = res["api_response"]

        expected_data = {
            "values": {
                "file": {
                    "file1.txt": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",  # This is example content.
                    "file2.txt": "Q29udGVudCBleGFtcGxlIGlzIHRoaXMu",  # Content example is this.
                },
            },
            "schema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "file": {
                        "type": "object",
                        "properties": {
                            "file1.txt": {"type": "string", "format": "base64"},
                            "file2.txt": {"type": "string", "format": "base64"},
                        },
                        "required": ["file1.txt", "file2.txt"],
                        "additionalProperties": False,
                    }
                },
                "additionalProperties": False,
                "required": [],
            },
        }

        self.assertEqual(res_json["data"], expected_data)

    def test_required_in_schema_is_empty_if_select_boxes_component_unfilled(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "values": [
                        {"label": "Option 1", "value": "option1"},
                        {"label": "Option 2", "value": "option2"},
                    ],
                },
            ],
            completed=True,
            submitted_data={"selectboxes": {}},
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["selectboxes"],
        )

        res = json_plugin.register_submission(submission, json_form_options)

        self.assertEqual(
            glom(res, "api_response.data.schema.properties.selectboxes.required"), []
        )

    def test_select_component_with_form_variable_as_data_source(self):

        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Select",
                    "key": "select",
                    "type": "select",
                    "multiple": True,
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "valuesForSelect"},
                    },
                    "data": {
                        "values": [],
                        "json": "",
                        "url": "",
                        "resource": "",
                        "custom": "",
                    },
                },
            ],
            completed=True,
            submitted_data={"select": ["A", "C"]},
        )

        FormVariableFactory.create(
            form=submission.form,
            name="Values for select",
            key="valuesForSelect",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["select"],
        )

        res = json_plugin.register_submission(submission, json_form_options)

        self.assertEqual(
            glom(res, "api_response.data.schema.properties.select.items.enum"),
            ["A", "B", "C", ""],
        )

    def test_select_boxes_component_with_form_variable_as_data_source(self):

        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "openForms": {
                        "dataSrc": "variable",
                        "translations": {},
                        "itemsExpression": {"var": "valuesForSelectBoxes"},
                    },
                    "values": [],
                },
            ],
            completed=True,
            submitted_data={"selectBoxes": {"A": True, "B": False, "C": True}},
        )

        FormVariableFactory.create(
            form=submission.form,
            name="Values for select boxes",
            key="valuesForSelectBoxes",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["selectBoxes"],
        )

        res = json_plugin.register_submission(submission, json_form_options)

        expected_schema = {
            "title": "Select Boxes",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "A": {"type": "boolean"},
                "B": {"type": "boolean"},
                "C": {"type": "boolean"},
            },
            "required": ["A", "B", "C"],
        }

        self.assertEqual(
            glom(res, "api_response.data.schema.properties.selectBoxes"),
            expected_schema
        )

    def test_select_boxes_schema_required_is_empty_when_no_data_is_submitted(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "A", "value": "a"},
                        {"label": "B", "value": "b"},
                        {"label": "C", "value": "c"},
                    ],
                },
            ],
            completed=True,
            submitted_data={"selectBoxes": {}},
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["selectBoxes"],
        )

        res = json_plugin.register_submission(submission, json_form_options)

        self.assertEqual(
            glom(res, "api_response.data.schema.properties.selectBoxes.required"),
            [],
        )

    def test_radio_component_with_form_variable_as_data_source(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "openForms": {
                        "dataSrc": "variable",
                        "translations": {},
                        "itemsExpression": {"var": "valuesForRadio"},
                    },
                    "values": [],
                },
            ],
            completed=True,
            submitted_data={"radio": "A"},
        )

        FormVariableFactory.create(
            form=submission.form,
            name="Values for radio",
            key="valuesForRadio",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        set_submission_reference(submission)

        json_form_options = dict(
            service=(ServiceFactory(api_root="http://localhost:80/")),
            relative_api_endpoint="json_plugin",
            form_variables=["radio"],
        )

        res = json_plugin.register_submission(submission, json_form_options)

        self.assertEqual(
            glom(res, "api_response.data.schema.properties.radio.enum"),
            ["A", "B", "C", ""],
        )
