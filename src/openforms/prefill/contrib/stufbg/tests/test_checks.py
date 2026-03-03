from unittest.mock import patch

from django.test import TestCase

import requests_mock
from requests import RequestException

from stuf.stuf_bg.exceptions import InvalidPluginConfiguration
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_bg.tests.mixins import StUFBGAssertionsMixin
from stuf.tests.factories import StufServiceFactory

from ..plugin import StufBgPrefill


class StufBgCheckTests(StUFBGAssertionsMixin, TestCase):
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

    @requests_mock.Mocker()
    def test_check_config_ok_not_found(self, m):
        # fault is part of SOAP so not able/necessary to test this
        content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgNotFoundResponse.xml",
            self.stuf_bg_service,
        )
        m.register_uri(requests_mock.ANY, requests_mock.ANY, content=content)

        try:
            self.plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config should have passed checks") from exc

    @requests_mock.Mocker()
    def test_check_config_ok_no_object(self, m):
        content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgNoObjectResponse.xml",
            self.stuf_bg_service,
        )

        # assert response is valid
        self.assertSoapBodyIsValid(content)

        m.register_uri(requests_mock.ANY, requests_mock.ANY, content=content)

        try:
            self.plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config should have passed checks") from exc

    @requests_mock.Mocker()
    def test_check_config_other_error(self, m):
        # fault is part of SOAP so not able/necessary to test this
        content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgErrorResponse.xml",
            self.stuf_bg_service,
        )

        m.register_uri(requests_mock.ANY, requests_mock.ANY, content=content)

        with self.assertRaises(InvalidPluginConfiguration):
            self.plugin.check_config()

    @requests_mock.Mocker()
    def test_check_config_some_unexpected_random_result(self, m):
        content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponseWithVoorvoegsel.xml",
            self.stuf_bg_service,
        )

        # assert response is valid
        self.assertSoapBodyIsValid(content)

        m.register_uri(requests_mock.ANY, requests_mock.ANY, content=content)

        with self.assertRaises(InvalidPluginConfiguration):
            self.plugin.check_config()
