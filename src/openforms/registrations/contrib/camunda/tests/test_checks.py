"""
Test the Camunda-plugin specific extra API endpoints.

These endpoints are only used in the form designer.
"""
from unittest.mock import patch

from django.test import TestCase
from django.utils.translation import gettext as _

import requests_mock
from django_camunda.models import CamundaConfig

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..checks import check_config


@patch("openforms.registrations.contrib.camunda.checks.CamundaConfig.get_solo")
class PluginChecksTests(TestCase):
    def test_not_enabled(self, mock_get_solo):
        mock_get_solo.return_value = CamundaConfig(enabled=False)

        err = _("Camunda integration is not enabled in the configuration.")
        with self.assertRaisesMessage(InvalidPluginConfiguration, err):
            check_config()

    @requests_mock.Mocker()
    def test_invalid_host(self, mock_get_solo, m):
        m.get(
            "https://camunda.example.com/camunda/engine-rest/version", status_code=404
        )
        mock_get_solo.return_value = CamundaConfig(
            enabled=True,
            root_url="https://camunda.example.com",
            rest_api_path="camunda/engine-rest/",
        )

        with self.assertRaises(InvalidPluginConfiguration) as ctx:
            check_config()

        self.assertIn("404", ctx.exception.args[0])

    @requests_mock.Mocker()
    def test_no_process_definitions(self, mock_get_solo, m):
        m.get(
            "https://camunda.example.com/camunda/engine-rest/version",
            json={"version": "dummy"},
        )
        m.get(
            "https://camunda.example.com/camunda/engine-rest/process-definition?sortBy=name&sortOrder=asc",
            json=[],
        )

        mock_get_solo.return_value = CamundaConfig(
            enabled=True,
            root_url="https://camunda.example.com",
            rest_api_path="camunda/engine-rest/",
        )

        err = _(
            "No process definitions found. The Camunda user may not have sufficient permissions."
        )
        with self.assertRaisesMessage(InvalidPluginConfiguration, err):
            check_config()
