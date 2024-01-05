from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..checks import BRKValidatorCheck
from ..models import BRKConfig
from .base import BRK_SERVICE


class ConfigCheckTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        self.config = BRKConfig(service=BRK_SERVICE)
        config_patcher = patch(
            "openforms.contrib.brk.client.BRKConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_no_brk_service_configured(self):
        self.config.service = None

        with self.assertRaises(InvalidPluginConfiguration):
            BRKValidatorCheck.check_config()

    @requests_mock.Mocker()
    def test_brk_check_error(self, m: requests_mock.Mocker):
        m.register_uri(requests_mock.ANY, requests_mock.ANY, status_code=400)

        with self.assertRaises(InvalidPluginConfiguration):
            BRKValidatorCheck.check_config()

        self.assertGreater(len(m.request_history), 0)

    @requests_mock.Mocker()
    def test_invalid_response_data_returned(self, m: requests_mock.Mocker):
        bad_responses = (
            [],
            {"_embedded": None},
            {"_embedded": []},
        )

        for response_json in bad_responses:
            with self.subTest(response_json=response_json):
                m.register_uri(
                    requests_mock.ANY,
                    requests_mock.ANY,
                    json=response_json,
                )

                with self.assertRaises(InvalidPluginConfiguration):
                    BRKValidatorCheck.check_config()

    @requests_mock.Mocker()
    def test_valid_brk_configuration(self, m: requests_mock.Mocker):
        m.get(
            "https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/kadastraalonroerendezaken?postcode=1234AB&huisnummer=1",
            json={"_embedded": {}},
        )

        try:
            BRKValidatorCheck.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc
