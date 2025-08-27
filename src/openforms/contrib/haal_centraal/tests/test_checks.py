from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.registry import register

plugin = register["haalcentraal"]


class ConfigCheckTests:
    # specify in subclasses
    version: BRPVersions

    # set in setUp
    config: HaalCentraalConfig

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        self.config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            ),
            brp_personen_version=self.version,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        global_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(),
        )
        self.config_mock = global_config_patcher.start()
        self.addCleanup(global_config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_undefined_service_raises_exception(self):
        with self.assertRaisesMessage(
            InvalidPluginConfiguration, _("Service not selected")
        ):
            plugin.check_config()

    def test_invalid_version_raises_exception(self):
        self.config.brp_personen_version = "0.999"
        assert self.config.brp_personen_version not in BRPVersions.values

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "No suitable client class configured for API version 0.999",
        ):
            plugin.check_config()

    def test_404_client_error_returns_None(self):
        result = plugin.check_config()
        self.assertIsNone(result)

    def test_generic_client_error_raises_exception(self):
        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()


class ConfigCheckV1Tests(ConfigCheckTests, SimpleTestCase):
    version = BRPVersions.v13

    def test_undefined_service_raises_exception(self):
        self.config.brp_personen_service = None
        super().test_undefined_service_raises_exception()

    def test_404_client_error_returns_None(self):
        self.requests_mock.get("https://personen/api/test", status_code=404)
        super().test_404_client_error_returns_None()

    def test_generic_client_error_raises_exception(self):
        self.requests_mock.get("https://personen/api/test", status_code=405)
        super().test_generic_client_error_raises_exception()


class ConfigCheckV2Tests(ConfigCheckTests, SimpleTestCase):
    version = BRPVersions.v20

    def test_undefined_service_raises_exception(self):
        self.config.brp_personen_service = None
        super().test_undefined_service_raises_exception()

    def test_404_client_error_returns_None(self):
        self.requests_mock.post("https://personen/api/personen", status_code=400)
        super().test_404_client_error_returns_None()

    def test_generic_client_error_raises_exception(self):
        self.requests_mock.post("https://personen/api/personen", status_code=405)
        super().test_generic_client_error_raises_exception()
