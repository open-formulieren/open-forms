from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..models import JSONConfig
from ..plugin import JSONRegistration


class ConfigCheckTests(TestCase):

    @patch("zgw_consumers.nlx.NLXClient.get")
    def test_config_check(self, mock_post):
        json_plugin = JSONRegistration("json_registration_plugin")

        config = JSONConfig(
            service=ServiceFactory(api_root="https://example.com/", api_connection_check_path="test")
        )

        with patch(
            "openforms.registrations.contrib.json.plugin.JSONConfig.get_solo",
            return_value=config
        ):
            json_plugin.check_config()
            mock_post.assert_called_once_with("test")

    def test_no_service_configured(self):
        config = JSONConfig(service=None)
        json_plugin = JSONRegistration("json_registration_plugin")

        with patch(
            "openforms.registrations.contrib.json.plugin.JSONConfig.get_solo",
            return_value=config
        ):
            self.assertRaises(InvalidPluginConfiguration, json_plugin.check_config)
