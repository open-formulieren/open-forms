from django.test import SimpleTestCase

import requests_mock
from privates.test import temp_private_root

from openforms.contrib.kvk.tests.base import KVKTestMixin
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..plugin import KVK_KVKNumberPrefill

plugin = KVK_KVKNumberPrefill("kvk")


@temp_private_root()
class KVKPrefillConfigCheckTests(KVKTestMixin, SimpleTestCase):
    def test_no_kvk_service_configured(self):
        self.config_mock.return_value.search_service = None
        self.config_mock.return_value.profile_service = None

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_check_config_ok(self, m):
        m.get(
            "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
            json={
                "kvkNummer": "68750110",
                # rest of the keys omitted, see
                # ``src/openforms/contrib/kvk/api_models/basisprofiel.py`` for the
                # data model
            },
        )

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

    @requests_mock.Mocker()
    def test_kvk_check_error(self, m):
        m.register_uri(requests_mock.ANY, requests_mock.ANY, status_code=404)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

        self.assertGreater(len(m.request_history), 0)

    @requests_mock.Mocker()
    def test_invalid_response_data_returned(self, m):
        bad_responses = (
            [],
            {},
            {"kvkNummer": "wrong-number"},
        )

        for response_json in bad_responses:
            with self.subTest(response_json=response_json):
                m.register_uri(
                    requests_mock.ANY,
                    requests_mock.ANY,
                    json=response_json,
                )

                with self.assertRaises(InvalidPluginConfiguration):
                    plugin.check_config()
