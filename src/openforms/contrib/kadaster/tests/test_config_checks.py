from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..config_check import BAGCheck, LocatieServerCheck
from ..models import KadasterApiConfig


class ConfigCheckTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        self.config = KadasterApiConfig(
            search_service=ServiceFactory.build(
                api_root="https://kadaster/",
            )
        )
        config_patcher = patch(
            "openforms.contrib.kadaster.clients.KadasterApiConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    @requests_mock.Mocker()
    def test_locatie_server_check_error(self, m):
        m.register_uri(requests_mock.ANY, requests_mock.ANY, status_code=400)

        with self.assertRaises(InvalidPluginConfiguration):
            LocatieServerCheck.check_config()

    @requests_mock.Mocker()
    def test_bag_check_error(self, m):
        # just assign whatever service, we mock the actual calls anyway
        self.config.bag_service = self.config.search_service
        m.register_uri(requests_mock.ANY, requests_mock.ANY, status_code=400)

        with self.assertRaises(InvalidPluginConfiguration):
            BAGCheck.check_config()

        self.assertGreater(len(m.request_history), 0)

    def test_no_bag_client_configured(self):
        assert self.config.bag_service is None

        with self.assertRaises(InvalidPluginConfiguration):
            BAGCheck.check_config()
