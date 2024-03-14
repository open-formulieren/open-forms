from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..checks import KVKRemoteValidatorCheck
from ..models import KVKConfig
from .base import KVK_SERVICE


class ConfigCheckTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        self.config = KVKConfig(search_service=KVK_SERVICE)
        config_patcher = patch(
            "openforms.contrib.kvk.client.KVKConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_no_kvk_service_configured(self):
        self.config.search_service = None

        with self.assertRaises(InvalidPluginConfiguration):
            KVKRemoteValidatorCheck.check_config()

    @requests_mock.Mocker()
    def test_kvk_check_error(self, m):
        m.register_uri(requests_mock.ANY, requests_mock.ANY, status_code=400)

        with self.assertRaises(InvalidPluginConfiguration):
            KVKRemoteValidatorCheck.check_config()

        self.assertGreater(len(m.request_history), 0)

    @requests_mock.Mocker()
    def test_invalid_response_data_returned(self, m):
        bad_responses = (
            [],
            {"resultaten": None},
            {"resultaten": []},
            {
                "resultaten": [
                    {
                        "kvkNummer": "something-else",
                    }
                ]
            },
        )

        for response_json in bad_responses:
            with self.subTest(response_json=response_json):
                m.register_uri(
                    requests_mock.ANY,
                    requests_mock.ANY,
                    json=response_json,
                )

                with self.assertRaises(InvalidPluginConfiguration):
                    KVKRemoteValidatorCheck.check_config()

    @requests_mock.Mocker()
    def test_valid_kvk_configuration(self, m):
        m.get(
            "https://api.kvk.nl/test/api/v2/zoeken?kvkNummer=68750110",
            json={"resultaten": [{"kvkNummer": "68750110"}]},
        )

        try:
            KVKRemoteValidatorCheck.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc
