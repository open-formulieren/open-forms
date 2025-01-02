from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import JSONConfig
from ..plugin import JSONRegistration

VCR_TEST_FILES = Path(__file__).parent / "files"


class ConfigCheckTests(OFVCRMixin, TestCase):

    VCR_TEST_FILES = VCR_TEST_FILES

    def test_config_check_happy_flow(self):
        json_plugin = JSONRegistration("json_registration_plugin")

        config = JSONConfig(
            service=ServiceFactory(
                api_root="http://localhost:80/",
                api_connection_check_path="test_connection",
            )
        )

        with patch(
            "openforms.registrations.contrib.json.plugin.JSONConfig.get_solo",
            return_value=config,
        ):
            json_plugin.check_config()

    def test_no_service_configured(self):
        config = JSONConfig(service=None)
        json_plugin = JSONRegistration("json_registration_plugin")

        with patch(
            "openforms.registrations.contrib.json.plugin.JSONConfig.get_solo",
            return_value=config,
        ):
            self.assertRaises(InvalidPluginConfiguration, json_plugin.check_config)

    def test_invalid_response_from_api_test_connection_endpoint(self):
        json_plugin = JSONRegistration("json_registration_plugin")

        config = JSONConfig(
            service=ServiceFactory(
                api_root="http://localhost:80/",
                api_connection_check_path="fake_endpoint",
            )
        )

        with patch(
            "openforms.registrations.contrib.json.plugin.JSONConfig.get_solo",
            return_value=config,
        ):
            self.assertRaises(InvalidPluginConfiguration, json_plugin.check_config)
