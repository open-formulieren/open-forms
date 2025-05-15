from contextlib import contextmanager
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from requests import RequestException

from stuf.stuf_bg.exceptions import InvalidPluginConfiguration
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_bg.tests.utils import get_mock_response_content
from stuf.tests.factories import StufServiceFactory

from ..plugin import StufBgPrefill


@contextmanager
def mock_stufbg_make_request(template: str):
    content = get_mock_response_content(template)
    with requests_mock.Mocker() as m:
        m.register_uri(requests_mock.ANY, requests_mock.ANY, content=content)
        yield


class StufBgCheckTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.stuf_bg_service = StufServiceFactory.create()

    def setUp(self) -> None:
        super().setUp()

        self.plugin = StufBgPrefill("test-plugin")

        # mock out django-solo interface (we don't have to deal with caches then)
        self.config = StufBGConfig(service=self.stuf_bg_service)
        stufbg_config_patcher = patch(
            "openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo",
            return_value=self.config,
        )
        stufbg_config_patcher.start()
        self.addCleanup(stufbg_config_patcher.stop)

    def test_no_service_configured(self):
        self.config.service = None

        with self.assertRaises(InvalidPluginConfiguration):
            self.plugin.check_config()

    def test_check_config_exception(self):
        with patch(
            "stuf.stuf_bg.client.Client.get_values_for_attributes",
            side_effect=RequestException(),
        ):
            with self.assertRaises(InvalidPluginConfiguration):
                self.plugin.check_config()

    @requests_mock.Mocker()
    def test_check_config_invalid_xml_returned(self, m):
        m.register_uri(requests_mock.ANY, requests_mock.ANY, json={"not": "xml"})

        with self.assertRaises(InvalidPluginConfiguration):
            self.plugin.check_config()

    def test_check_config_ok_not_found(self):
        try:
            with mock_stufbg_make_request("StufBgNotFoundResponse.xml"):
                self.plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config should have passed checks") from exc

    def test_check_config_ok_no_object(self):
        try:
            with mock_stufbg_make_request("StufBgNoObjectResponse.xml"):
                self.plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config should have passed checks") from exc

    def test_check_config_other_error(self):
        with self.assertRaises(InvalidPluginConfiguration):
            with mock_stufbg_make_request("StufBgErrorResponse.xml"):
                self.plugin.check_config()

    def test_check_config_some_unexpected_random_result(self):
        with self.assertRaises(InvalidPluginConfiguration):
            with mock_stufbg_make_request("StufBgResponseWithVoorvoegsel.xml"):
                self.plugin.check_config()
