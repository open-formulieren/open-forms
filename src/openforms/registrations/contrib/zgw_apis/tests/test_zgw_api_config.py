from django.test import TestCase

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import ZGWRegistration
from .factories import ZGWApiGroupConfigFactory


class ZGWApisConfigCheckTests(OFVCRMixin, TestCase):
    def test_check_config(self):
        ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        plugin = ZGWRegistration("zgw")

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("docker compose setup should be valid") from exc

        requests = self.cassette.requests
        # zaken api call
        # documenten api call
        # catalogi api call
        self.assertEqual(len(requests), 3)

    def test_check_config_request_error(self):
        ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        plugin = ZGWRegistration("zgw")

        with self.vcr_raises():
            with self.assertRaises(InvalidPluginConfiguration):
                plugin.check_config()

    def test_check_config_random_error(self):
        class CustomException(Exception):
            pass

        ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        plugin = ZGWRegistration("zgw")

        with self.vcr_raises(CustomException):
            with self.assertRaises(InvalidPluginConfiguration):
                plugin.check_config()
