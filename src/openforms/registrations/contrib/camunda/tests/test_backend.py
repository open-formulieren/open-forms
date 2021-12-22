import uuid
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from django_camunda.camunda_models import ProcessDefinition
from django_camunda.models import CamundaConfig
from privates.test import temp_private_root

from openforms.submissions.tests.factories import SubmissionFactory

from ..plugin import VARS, CamundaRegistration, serialize_variables


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class InitialRegistrationTests(TestCase):
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
        }
        plugin = CamundaRegistration("camunda")

        result = plugin.register_submission(
            self.submission, registration_backend_options
        )

        mock_start_process.assert_called_once_with(
            process_key="invoice",
            variables=serialize_variables(VARS),
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
        }
        plugin = CamundaRegistration("camunda")

        result = plugin.register_submission(
            self.submission, registration_backend_options
        )

        mock_start_process.assert_called_once_with(
            process_id="invoice:2:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
            variables=serialize_variables(VARS),
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
