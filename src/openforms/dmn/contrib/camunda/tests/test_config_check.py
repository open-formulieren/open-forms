from unittest.mock import patch

from django.test import TestCase
from django.utils.translation import gettext as _

import requests_mock
from django_camunda.models import CamundaConfig

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ....registry import register

plugin = register["camunda7"]


def patch_camunda_config(**kwargs):
    config = CamundaConfig(**kwargs)
    patcher = patch(
        "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
        return_value=config,
    )
    return patcher


class ConfigCheckTests(TestCase):
    def setUp(self):
        super().setUp()

        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)

    @patch_camunda_config(enabled=False)
    def test_camunda_disabled(self, mock_get_solo):
        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            _("Camunda integration is not enabled in the configuration."),
        ):
            plugin.check_config()

    @patch_camunda_config(enabled=True, rest_api_path="engine-rest/")
    def test_invalid_client_config(self, mock_get_solo):
        with self.assertRaises(InvalidPluginConfiguration) as error:
            plugin.check_config()

        self.assertIn("No mock address", error.exception.args[0])

    @patch_camunda_config(enabled=True, rest_api_path="engine-rest/")
    def test_generic_error_while_retrieving_definitions(self, mock_get_solo):
        self.requests_mock.get(
            "https://camunda.example.com/engine-rest/version",
            json={"version": "7.16.0"},
        )

        with self.subTest("Some network issue"):
            # the error is triggered by requests_mock
            with self.assertRaisesMessage(
                InvalidPluginConfiguration,
                _("Could not retrieve the available decision definitions."),
            ):
                plugin.check_config()

        with self.subTest("Invalid permissions"):
            # the error is triggered by requests_mock
            self.requests_mock.get(
                "https://camunda.example.com/engine-rest/decision-definition",
                json={"type": "RestException"},
                status_code=403,
            )
            with self.assertRaisesMessage(
                InvalidPluginConfiguration,
                _("Could not retrieve the available decision definitions."),
            ):
                plugin.check_config()

    @patch_camunda_config(enabled=True, rest_api_path="engine-rest/")
    def test_no_definitions_found(self, mock_get_solo):
        self.requests_mock.get(
            "https://camunda.example.com/engine-rest/version",
            json={"version": "7.16.0"},
        )
        self.requests_mock.get(
            "https://camunda.example.com/engine-rest/decision-definition", json=[]
        )
        msg = _(
            "No decision definitions found. The Camunda user may not have sufficient permissions."
        )
        with self.assertRaisesMessage(InvalidPluginConfiguration, msg):
            plugin.check_config()
