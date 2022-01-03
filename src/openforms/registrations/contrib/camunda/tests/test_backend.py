import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from django_camunda.camunda_models import ProcessDefinition
from django_camunda.models import CamundaConfig
from privates.test import temp_private_root

from openforms.submissions.tests.factories import SubmissionFactory

from ....exceptions import RegistrationFailed
from ..plugin import CamundaRegistration, serialize_variables


class CamundaMixin:
    def setUp(self):
        super().setUp()

        # set up a CamundaConfig mocker
        config_patcher = patch("django_camunda.client.CamundaConfig.get_solo")
        self.config_mock = config_patcher.start()
        self.config_mock.return_value = CamundaConfig(
            enabled=True,
            root_url="https://camunda.example.com",
            rest_api_path="engine-rest/",
        )
        self.addCleanup(config_patcher.stop)


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class InitialRegistrationTests(CamundaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "type": "currency",
                    "key": "amount",
                },
                {
                    "type": "textfield",
                    "key": "invoiceCategory",
                },
            ],
            submitted_data={
                "amount": "25.00",
                "invoiceCategory": "Misc",
            },
            with_report=False,
            form__registration_backend="camunda",
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_submission_with_camunda_backend_latest_version(
        self, m, mock_start_process
    ):
        mock_start_process.return_value = {
            "instance_id": "a027768e-92f9-4003-b28f-ac9500fbd39d",
            "instance_url": (
                "https://camunda.example.com/engine-rest/"
                "process-instance/a027768e-92f9-4003-b28f-ac9500fbd39d"
            ),
        }
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
            "process_variables": [],
        }
        plugin = CamundaRegistration("camunda")

        result = plugin.register_submission(
            self.submission, registration_backend_options
        )

        mock_start_process.assert_called_once_with(
            process_key="invoice",
            variables={},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(
            result,
            {
                "instance": {
                    "id": "a027768e-92f9-4003-b28f-ac9500fbd39d",
                    "url": (
                        "https://camunda.example.com/engine-rest/"
                        "process-instance/a027768e-92f9-4003-b28f-ac9500fbd39d"
                    ),
                }
            },
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_submission_with_camunda_backend_pinned_version(
        self, m, mock_start_process
    ):
        mock_start_process.return_value = {
            "instance_id": "a027768e-92f9-4003-b28f-ac9500fbd39d",
            "instance_url": (
                "https://camunda.example.com/engine-rest/"
                "process-instance/a027768e-92f9-4003-b28f-ac9500fbd39d"
            ),
        }
        mock_data = [
            ProcessDefinition(
                id="unrelated:1:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                key="unrelated",
                name="Process 1",
                category="",
                version=1,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
            ProcessDefinition(
                id="invoice:2:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                key="invoice",
                name="Process 1",
                category="",
                version=2,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
            ProcessDefinition(
                id="invoice:1:11714efa-b5a2-45a3-904b-31281db1539e",
                key="invoice",
                name="Process 2",
                category="",
                version=1,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
        ]
        get_process_defs_patcher = patch(
            "openforms.registrations.contrib.camunda.plugin.get_process_definitions",
            return_value=mock_data,
        )
        get_process_defs_patcher.start()
        self.addCleanup(get_process_defs_patcher.stop)
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": 2,  # indicates latest version
            "process_variables": [],
        }
        plugin = CamundaRegistration("camunda")

        result = plugin.register_submission(
            self.submission, registration_backend_options
        )

        mock_start_process.assert_called_once_with(
            process_id="invoice:2:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
            variables={},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(
            result,
            {
                "instance": {
                    "id": "a027768e-92f9-4003-b28f-ac9500fbd39d",
                    "url": (
                        "https://camunda.example.com/engine-rest/"
                        "process-instance/a027768e-92f9-4003-b28f-ac9500fbd39d"
                    ),
                }
            },
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_process_version_does_not_exist(self, m, mock_start_process):
        get_process_defs_patcher = patch(
            "openforms.registrations.contrib.camunda.plugin.get_process_definitions",
            return_value=[],
        )
        get_process_defs_patcher.start()
        self.addCleanup(get_process_defs_patcher.stop)
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": 2,  # indicates latest version
        }
        plugin = CamundaRegistration("camunda")

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(self.submission, registration_backend_options)

        mock_start_process.assert_not_called()

    def test_camunda_http_500(self, m):
        m.post(
            "https://camunda.example.com/engine-rest/process-definition/key/invoice/start",
            status_code=500,
            json={"error": "information"},
        )
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
        }
        plugin = CamundaRegistration("camunda")

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(self.submission, registration_backend_options)

        start_process_request = m.last_request
        request_body = start_process_request.json()
        self.assertIsInstance(request_body, dict)

    def test_camunda_http_400(self, m):
        m.post(
            "https://camunda.example.com/engine-rest/process-definition/key/invoice/start",
            status_code=400,
            json={"error": "information"},
        )
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
        }
        plugin = CamundaRegistration("camunda")

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(self.submission, registration_backend_options)

        start_process_request = m.last_request
        request_body = start_process_request.json()
        self.assertIsInstance(request_body, dict)


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class MappedProcessVariableTests(CamundaMixin, TestCase):
    """
    Test that form values are mapped correctly onto process variables.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "type": "currency",
                    "key": "currency",
                },
                {
                    "type": "textfield",
                    "key": "invoiceCategory",
                },
                {
                    "type": "textfield",
                    "key": "extra",
                },
            ],
            submitted_data={
                "currency": "25.00",
                "invoiceCategory": "Misc",
            },
            with_report=False,
            form__registration_backend="camunda",
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_submission_with_mapped_variables(self, m, mock_start_process):
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
            "process_variables": [
                {
                    "enabled": True,
                    "component_key": "currency",
                    "alias": "amount",
                },
                {
                    "enabled": True,
                    "component_key": "invoiceCategory",
                    "alias": "",
                },
            ],
            "complex_process_variables": [],
        }
        plugin = CamundaRegistration("camunda")

        plugin.register_submission(self.submission, registration_backend_options)

        mock_start_process.assert_called_once_with(
            process_key="invoice",
            variables=serialize_variables(
                {
                    "amount": Decimal("25.00"),
                    "invoiceCategory": "Misc",
                }
            ),
        )


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class ComplexProcessVariableTests(CamundaMixin, TestCase):
    """
    Assert that complex variables are correctly mapped to JSON variables in Camunda.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "type": "currency",
                    "key": "currency",
                },
                {
                    "type": "textfield",
                    "key": "text",
                },
                {
                    "type": "number",
                    "key": "number",
                },
            ],
            submitted_data={
                "currency": "25.00",
                "text": "Misc",
                "number": 12.50,
            },
            with_report=False,
            form__registration_backend="camunda",
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_json_object_type(self, m, mock_start_process):
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
            "process_variables": [],
            "complex_process_variables": [
                {
                    "enabled": True,
                    "alias": "variable_1",
                    "type": "object",
                    "definition": {
                        "nested_object": {
                            "source": "manual",
                            "type": "object",
                            "definition": {
                                "amount": {
                                    "source": "component",
                                    "definition": {"var": "currency"},
                                },
                                "fixed_string": {
                                    "source": "manual",
                                    "type": "string",
                                    "definition": "a fixed string",
                                },
                            },
                        },
                        "nestedList": {
                            "source": "manual",
                            "type": "array",
                            "definition": [
                                {
                                    "source": "manual",
                                    "type": "null",
                                    "definition": None,
                                },
                                {
                                    "source": "manual",
                                    "type": "array",
                                    "definition": [
                                        {
                                            "source": "component",
                                            "definition": {"var": "number"},
                                        }
                                    ],
                                },
                            ],
                        },
                    },
                }
            ],
        }
        plugin = CamundaRegistration("camunda")
        with self.subTest("validate data setup"):
            serializer = plugin.configuration_options(data=registration_backend_options)
            self.assertTrue(serializer.is_valid())

        plugin.register_submission(self.submission, registration_backend_options)

        expected_evaluated_value = {
            "nested_object": {
                "amount": "25.00",
                "fixed_string": "a fixed string",
            },
            "nestedList": [
                None,
                [12.50],
            ],
        }
        mock_start_process.assert_called_once_with(
            process_key="invoice",
            variables=serialize_variables(
                {
                    "variable_1": expected_evaluated_value,
                }
            ),
        )

    @patch("openforms.registrations.contrib.camunda.plugin.start_process")
    def test_json_array_type(self, m, mock_start_process):
        registration_backend_options = {
            "process_definition": "invoice",
            "process_definition_version": None,  # indicates latest version
            "process_variables": [],
            "complex_process_variables": [
                {
                    "enabled": True,
                    "alias": "variable_2",
                    "type": "array",
                    "definition": [
                        {
                            "source": "manual",
                            "type": "boolean",
                            "definition": False,
                        },
                    ],
                },
            ],
        }
        plugin = CamundaRegistration("camunda")
        with self.subTest("validate data setup"):
            serializer = plugin.configuration_options(data=registration_backend_options)
            self.assertTrue(serializer.is_valid())

        plugin.register_submission(self.submission, registration_backend_options)

        expected_evaluated_value = [False]
        mock_start_process.assert_called_once_with(
            process_key="invoice",
            variables=serialize_variables(
                {
                    "variable_2": expected_evaluated_value,
                }
            ),
        )
