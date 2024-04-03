from unittest.mock import patch

from django.test import SimpleTestCase

import requests
import requests_mock

from openforms.plugins.exceptions import InvalidPluginConfiguration
from stuf.stuf_zds.models import StufZDSConfig
from stuf.tests.factories import StufServiceFactory

from ..plugin import PLUGIN_IDENTIFIER, StufZDSRegistration


class ConfigCheckTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        self.config = StufZDSConfig(service=StufServiceFactory.build())
        patcher = patch(
            "stuf.stuf_zds.client.StufZDSConfig.get_solo",
            return_value=self.config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_service_configured(self):
        self.config.service = None
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_failing_request(self, m):
        m.post(requests_mock.ANY, exc=requests.ConnectionError("nope"))
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()
