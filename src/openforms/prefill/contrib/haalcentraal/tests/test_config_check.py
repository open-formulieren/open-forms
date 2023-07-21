from typing import Literal
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ....registry import register
from ..constants import HaalCentraalVersion
from ..models import HaalCentraalConfig

plugin = register["haalcentraal"]


class ConfigCheckTests:
    # specify in subclasses
    version: HaalCentraalVersion
    schema_yaml_name: Literal["personen", "personen-v2"]
    service: Service
    config: HaalCentraalConfig

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        self.config = HaalCentraalConfig(
            version=self.version,
            service=self.service,
        )
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        mock_service_oas_get(
            self.requests_mock,
            url=self.service.api_root,
            service=self.schema_yaml_name,
            oas_url=self.service.oas,
        )
        self.addCleanup(self.requests_mock.stop)  # type: ignore

        # ensure the schema cache is cleared before and after each test
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)  # type: ignore

    def test_undefined_service_raises_exception(self):
        with self.assertRaisesMessage(
            InvalidPluginConfiguration, _("Service not selected")
        ):
            plugin.check_config()

    def test_404_client_error_returns_None(self):
        result = plugin.check_config()
        self.assertIsNone(result)

    def test_generic_client_error_raises_exception(self):
        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            _("Client error: {exception}").format(exception={"status": 405}),
        ):
            plugin.check_config()


class ConfigCheckV1Tests(ConfigCheckTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()

    def test_undefined_service_raises_exception(self):
        self.config.service = None
        self.requests_mock.get(
            "https://personen/api/test", status_code=404, json={"status": 404}
        )
        super().test_undefined_service_raises_exception()

    def test_404_client_error_returns_None(self):
        self.requests_mock.get(
            "https://personen/api/test", status_code=404, json={"status": 404}
        )
        super().test_404_client_error_returns_None()

    def test_generic_client_error_raises_exception(self):
        self.requests_mock.get(
            "https://personen/api/test", status_code=405, json={"status": 405}
        )
        super().test_generic_client_error_raises_exception()


class ConfigCheckV2Tests(ConfigCheckTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()

    def test_undefined_service_raises_exception(self):
        self.config.service = None
        self.requests_mock.post(
            "https://personen/api/test", status_code=400, json={"status": 400}
        )
        super().test_undefined_service_raises_exception()

    def test_404_client_error_returns_None(self):
        self.requests_mock.post(
            "https://personen/api/test", status_code=400, json={"status": 400}
        )
        super().test_404_client_error_returns_None()

    def test_generic_client_error_raises_exception(self):
        self.requests_mock.post(
            "https://personen/api/test", status_code=405, json={"status": 405}
        )
        super().test_generic_client_error_raises_exception()
