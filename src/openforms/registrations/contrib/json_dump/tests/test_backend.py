import unittest
from base64 import b64decode
from pathlib import Path

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase

from freezegun import freeze_time
from requests import RequestException
from zgw_consumers.test.factories import ServiceFactory

from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import FormVersionFactory
from openforms.submissions.tests.factories import (
    FormVariableFactory,
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..config import JSONDumpOptions
from ..plugin import JSONDumpRegistration

VCR_TEST_FILES = Path(__file__).parent / "files"


class JSONDumpBackendTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = VCR_TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = ServiceFactory.create(api_root="http://localhost:80/")

    def test_submission_happy_flow(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textfield"},
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
            with_public_registration_reference=True,
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.steps[0],
            file_name="test_file.txt",
            original_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["firstName", "file", "auth_bsn"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        expected_values = {
            # Note that `lastName` is not included here as it wasn't specified in the variables
            "auth_bsn": "123456789",
            "firstName": "We Are",
            "file": {
                "file_name": "test_file.txt",
                "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",
            },
        }
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "auth_bsn": {
                    "title": "BSN",
                    "description": (
                        "Uniquely identifies the authenticated person. This "
                        "value follows the rules for Dutch social security "
                        "numbers."
                    ),
                    "type": "string",
                    "pattern": "^\\d{9}$",
                    "format": "nl-bsn",
                },
                "firstName": {"title": "Firstname", "type": "string"},
                "file": {
                    "title": "File",
                    "type": "object",
                    "properties": {
                        "file_name": {"type": "string"},
                        "content": {"type": "string", "format": "base64"},
                    },
                    "required": ["file_name", "content"],
                    "additionalProperties": False,
                },
            },
            "required": ["firstName", "file", "auth_bsn"],
            "additionalProperties": False,
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )

        with self.subTest("attachment content encoded"):
            decoded_content = b64decode(
                result["api_response"]["data"]["values"]["file"]["content"]
            )
            self.assertEqual(decoded_content, b"This is example content.")

    def test_exception_raised_when_service_returns_unexpected_status_code(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textfield"},
                {"key": "lastName", "type": "textfield"},
            ],
            completed=True,
            submitted_data={"firstName": "We Are", "lastName": "Checking"},
            bsn="123456789",
            with_public_registration_reference=True,
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "fake_endpoint",
            "variables": ["firstName", "auth_bsn"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        with self.assertRaises(RequestException):
            json_plugin.register_submission(submission, options)

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
            with_public_registration_reference=True,
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.steps[0],
            file_name="file1.txt",
            original_name="file1.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.steps[0],
            file_name="file2.txt",
            original_name="file2.txt",
            content_type="application/text",
            content__data=b"Content example is this.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["file"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        expected_values = {
            "file": [
                {
                    "file_name": "file1.txt",
                    "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",  # This is example content.
                },
                {
                    "file_name": "file2.txt",
                    "content": "Q29udGVudCBleGFtcGxlIGlzIHRoaXMu",  # Content example is this.
                },
            ],
        }
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "file": {
                    "title": "File",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_name": {"type": "string"},
                            "content": {"type": "string", "format": "base64"},
                        },
                        "required": ["file_name", "content"],
                        "additionalProperties": False,
                    },
                }
            },
            "additionalProperties": False,
            "required": ["file"],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )

    def test_one_file_upload_for_multiple_files_component(self):
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
                    }
                ],
            },
            with_public_registration_reference=True,
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.steps[0],
            file_name="file1.txt",
            original_name="file1.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["file"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        expected_values = {
            "file": [
                {
                    "file_name": "file1.txt",
                    "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",  # This is example content.
                },
            ],
        }
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "file": {
                    "title": "File",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_name": {"type": "string"},
                            "content": {"type": "string", "format": "base64"},
                        },
                        "required": ["file_name", "content"],
                        "additionalProperties": False,
                    },
                }
            },
            "additionalProperties": False,
            "required": ["file"],
        }

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )

    def test_no_file_upload_for_single_file_component(self):
        submission = SubmissionFactory.from_components(
            [{"key": "file", "type": "file"}],
            completed=True,
            submitted_data={
                "file": [],
            },
            with_public_registration_reference=True,
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["file"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        expected_values = {"file": None}
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "file": {
                    "title": "File",
                    "type": "null",
                },
            },
            "additionalProperties": False,
            "required": ["file"],
        }

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )

    def test_no_file_upload_for_multiple_files_component(self):
        submission = SubmissionFactory.from_components(
            [{"key": "file", "type": "file", "multiple": True}],
            completed=True,
            submitted_data={
                "file": [],
            },
            with_public_registration_reference=True,
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["file"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        expected_values = {"file": []}
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "file": {
                    "title": "File",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_name": {"type": "string"},
                            "content": {"type": "string", "format": "base64"},
                        },
                        "required": [],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["file"],
            "additionalProperties": False,
        }

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )

    def test_path_traversal_attack(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textfield"},
                {"key": "lastName", "type": "textfield"},
            ],
            completed=True,
            submitted_data={
                "firstName": "We Are",
                "lastName": "Checking",
            },
            bsn="123456789",
            with_public_registration_reference=True,
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "..",
            "variables": ["firstName", "file", "auth_bsn"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        for path in ("..", "../foo", "foo/..", "foo/../bar"):
            with self.subTest(path), self.assertRaises(SuspiciousOperation):
                options["path"] = path
                json_plugin.register_submission(submission, options)

    def test_select_boxes_schema_required_is_empty_when_no_data_is_submitted(self):
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
            with_public_registration_reference=True,
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["selectboxes"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"][
                "selectboxes"
            ]["required"],
            [],
        )

    def test_select_component_with_manual_data_source(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Select",
                    "key": "select",
                    "type": "select",
                    "multiple": True,
                    "data": {
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                            {"value": "c", "label": "C"},
                        ],
                        "json": "",
                        "url": "",
                        "resource": "",
                        "custom": "",
                    },
                },
            ],
            completed=True,
            submitted_data={"select": ["a", "c"]},
            with_public_registration_reference=True,
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["select"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"]["select"][
                "items"
            ]["enum"],
            ["a", "b", "c", ""],
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
                        "dataSrc": DataSrcOptions.variable,
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
            with_public_registration_reference=True,
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

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["select"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"]["select"][
                "items"
            ]["enum"],
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
                        "dataSrc": DataSrcOptions.variable,
                        "translations": {},
                        "itemsExpression": {"var": "valuesForSelectBoxes"},
                    },
                    "values": [],
                },
            ],
            completed=True,
            submitted_data={"selectBoxes": {"A": True, "B": False, "C": True}},
            with_public_registration_reference=True,
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

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["selectBoxes"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

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
            result["api_response"]["data"]["values_schema"]["properties"][
                "selectBoxes"
            ],
            expected_schema,
        )

    def test_radio_component_with_manual_data_source(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "A", "value": "a"},
                        {"label": "B", "value": "b"},
                        {"label": "C", "value": "c"},
                    ],
                },
            ],
            completed=True,
            submitted_data={"radio": "b"},
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["radio"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"]["radio"][
                "enum"
            ],
            ["a", "b", "c", ""],
        )

    def test_radio_component_with_form_variable_as_data_source(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "openForms": {
                        "dataSrc": DataSrcOptions.variable,
                        "translations": {},
                        "itemsExpression": {"var": "valuesForRadio"},
                    },
                    "values": [],
                },
            ],
            completed=True,
            submitted_data={"radio": "A"},
            with_public_registration_reference=True,
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

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["radio"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"]["radio"][
                "enum"
            ],
            ["A", "B", "C", ""],
        )

    def test_components_with_form_variable_as_data_source_in_edit_grid_component(
        self,
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "repeatingGroup",
                    "label": "Repeating Group",
                    "type": "editgrid",
                    "components": [
                        {
                            "label": "Radio",
                            "key": "radio",
                            "type": "radio",
                            "openForms": {
                                "dataSrc": "variable",
                                "translations": {},
                                "itemsExpression": {"var": "valuesForComponent"},
                            },
                            "values": [],
                        },
                        {
                            "label": "Select",
                            "key": "select",
                            "type": "select",
                            "multiple": False,
                            "openForms": {
                                "dataSrc": "variable",
                                "itemsExpression": {"var": "valuesForComponent"},
                            },
                            "data": {
                                "values": [],
                                "json": "",
                                "url": "",
                                "resource": "",
                                "custom": "",
                            },
                        },
                        {
                            "label": "Select Boxes",
                            "key": "selectBoxes",
                            "type": "selectboxes",
                            "openForms": {
                                "dataSrc": "variable",
                                "translations": {},
                                "itemsExpression": {"var": "valuesForComponent"},
                            },
                            "values": [],
                        },
                    ],
                }
            ],
            completed=True,
            submitted_data={
                "repeatingGroup": [
                    {
                        "radio": "A",
                        "select": "B",
                        "selectBoxes": {"A": False, "B": False, "C": True},
                    }
                ]
            },
            with_public_registration_reference=True,
        )

        FormVariableFactory.create(
            form=submission.form,
            name="Values for components",
            key="valuesForComponent",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["repeatingGroup"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        with self.subTest("radio"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"]["properties"][
                    "repeatingGroup"
                ]["items"]["properties"]["radio"]["enum"],
                ["A", "B", "C", ""],
            )

        with self.subTest("select"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"]["properties"][
                    "repeatingGroup"
                ]["items"]["properties"]["select"]["enum"],
                ["A", "B", "C", ""],
            )

        with self.subTest("selectBoxes"):
            self.assertEqual(
                list(
                    result["api_response"]["data"]["values_schema"]["properties"][
                        "repeatingGroup"
                    ]["items"]["properties"]["selectBoxes"]["properties"].keys()
                ),
                ["A", "B", "C"],
            )

    @unittest.expectedFailure
    def test_nested_component_key(self):
        # TODO: will be fixed with issue 5041
        submission = SubmissionFactory.from_components(
            [
                {"key": "foo.bar", "type": "textfield", "label": "Nested key"},
            ],
            completed=True,
            submitted_data={"foo": {"bar": "baz"}},
            with_public_registration_reference=True,
        )

        json_plugin = JSONDumpRegistration("json_registration_plugin")

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["foo.bar"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(result["api_response"]["data"]["values"]["foo.bar"], "baz")
        self.assertEqual(
            result["api_response"]["data"]["values_schema"]["properties"]["foo.bar"][
                "type"
            ],
            "string",
        )

    @freeze_time("2025-01-30T13:05:00Z")
    def test_metadata(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textfield"},
                {"key": "lastName", "type": "textfield"},
            ],
            completed=True,
            submitted_data={
                "firstName": "We Are",
                "lastName": "Checking",
            },
            bsn="123456789",
            public_registration_reference="OF-ABC123",
        )
        FormVersionFactory.create(form=submission.form, description="Version 1.0")

        json_plugin = JSONDumpRegistration("json_registration_plugin")
        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": [],
            "fixed_metadata_variables": [
                "form_version",
                "public_reference",
                "registration_timestamp",
            ],
            "additional_metadata_variables": ["auth_type"],
        }
        result = json_plugin.register_submission(submission, options)
        assert result is not None

        expected_metadata = {
            "auth_type": "bsn",
            "form_version": "Version 1.0",
            "public_reference": "OF-ABC123",
            "registration_timestamp": "2025-01-30T13:05:00Z",
        }
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "additionalProperties": False,
            "properties": {
                "auth_type": {
                    "enum": ["bsn", "kvk", "pseudo", "employee_id", ""],
                    "title": "Authentication " "type",
                    "type": "string",
                },
                "form_version": {"title": "Form version", "type": "string"},
                "public_reference": {"title": "Public " "reference", "type": "string"},
                "registration_timestamp": {
                    "format": "date-time",
                    "title": "Registration " "timestamp",
                    "type": "string",
                },
            },
            "required": [
                "form_version",
                "public_reference",
                "registration_timestamp",
                "auth_type",
            ],
            "type": "object",
        }

        with self.subTest("metadata"):
            self.assertEqual(
                result["api_response"]["data"]["metadata"], expected_metadata
            )

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["metadata_schema"], expected_schema
            )

    def test_file_in_edit_grid_component(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "repeatingGroup",
                    "label": "Repeating Group",
                    "type": "editgrid",
                    "components": [
                        {
                            "key": "fileUploadInRepeating",
                            "label": "File upload",
                            "type": "file",
                            "multiple": True,
                        },
                    ],
                }
            ],
            completed=True,
            submitted_data={
                "repeatingGroup": [
                    {
                        "fileUploadInRepeating": [
                            {
                                "url": "http://example.com/api/v2/submissions/files/1",
                                "data": {
                                    "url": "https://example.com/api/v2/submissions/files/1",
                                    "form": "",
                                    "name": "test_file.txt",
                                    "size": 29,
                                    "baseUrl": "http://example.com/api/v2/",
                                    "project": "",
                                },
                                "name": "test_file.txt",
                                "size": 29,
                                "type": "text/plain",
                                "storage": "url",
                                "originalName": "test_file.txt",
                            },
                            {
                                "url": "https://example.com/api/v2/submissions/files/2",
                                "data": {
                                    "url": "https://example.com/api/v2/submissions/files/2",
                                    "form": "",
                                    "name": "test_file_2.txt",
                                    "size": 29,
                                    "baseUrl": "http://example.com/api/v2/",
                                    "project": "",
                                },
                                "name": "test_file_2.txt",
                                "size": 29,
                                "type": "text/plain",
                                "storage": "url",
                                "originalName": "test_file_2.txt",
                            },
                        ],
                    },
                    {
                        "fileUploadInRepeating": [
                            {
                                "url": "https://example.com/api/v2/submissions/files/3",
                                "data": {
                                    "url": "https://example.com/api/v2/submissions/files/3",
                                    "form": "",
                                    "name": "test_file_3.txt",
                                    "size": 29,
                                    "baseUrl": "http://example.com/api/v2/",
                                    "project": "",
                                },
                                "name": "test_file_3.txt",
                                "size": 29,
                                "type": "text/plain",
                                "storage": "url",
                                "originalName": "test_file_3.txt",
                            }
                        ],
                    },
                ]
            },
            bsn="123456789",
            with_public_registration_reference=True,
        )

        SubmissionFileAttachmentFactory.create(
            form_key="repeatingGroup",
            submission_step=submission.steps[0],
            file_name="test_file.txt",
            original_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_data_path="repeatingGroup.0.fileUploadInRepeating",
        )

        SubmissionFileAttachmentFactory.create(
            form_key="repeatingGroup",
            submission_step=submission.steps[0],
            file_name="test_file_2.txt",
            original_name="test_file_2.txt",
            content_type="application/text",
            content__data=b"This is example content 2.",
            _component_data_path="repeatingGroup.0.fileUploadInRepeating",
        )

        SubmissionFileAttachmentFactory.create(
            form_key="repeatingGroup",
            submission_step=submission.steps[0],
            file_name="test_file_3.txt",
            original_name="test_file_3.txt",
            content_type="application/text",
            content__data=b"This is example content 3.",
            _component_data_path="repeatingGroup.1.fileUploadInRepeating",
        )

        options: JSONDumpOptions = {
            "service": self.service,
            "path": "json_plugin",
            "variables": ["repeatingGroup"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }
        json_plugin = JSONDumpRegistration("json_registration_plugin")

        result = json_plugin.register_submission(submission, options)
        assert result is not None

        expected_values = {
            "repeatingGroup": [
                {
                    "fileUploadInRepeating": [
                        {
                            "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQu",
                            "file_name": "test_file.txt",
                        },
                        {
                            "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQgMi4=",
                            "file_name": "test_file_2.txt",
                        },
                    ]
                },
                {
                    "fileUploadInRepeating": [
                        {
                            "content": "VGhpcyBpcyBleGFtcGxlIGNvbnRlbnQgMy4=",
                            "file_name": "test_file_3.txt",
                        },
                    ]
                },
            ]
        }
        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "additionalProperties": False,
            "properties": {
                "repeatingGroup": {
                    "items": {
                        "additionalProperties": False,
                        "properties": {
                            "fileUploadInRepeating": {
                                "items": {
                                    "additionalProperties": False,
                                    "properties": {
                                        "content": {
                                            "format": "base64",
                                            "type": "string",
                                        },
                                        "file_name": {"type": "string"},
                                    },
                                    "required": ["file_name", "content"],
                                    "type": "object",
                                },
                                "title": "File upload",
                                "type": "array",
                            }
                        },
                        "required": ["fileUploadInRepeating"],
                        "type": "object",
                    },
                    "title": "Repeating Group",
                    "type": "array",
                }
            },
            "required": ["repeatingGroup"],
            "type": "object",
        }

        with self.subTest("values"):
            self.assertEqual(result["api_response"]["data"]["values"], expected_values)

        with self.subTest("schema"):
            self.assertEqual(
                result["api_response"]["data"]["values_schema"], expected_schema
            )
