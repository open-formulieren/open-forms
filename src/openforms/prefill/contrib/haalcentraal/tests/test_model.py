from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.models import Service

from openforms.prefill.contrib.haalcentraal.client import (
    HaalCentraalV1Client,
    HaalCentraalV2Client,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..constants import Attributes, AttributesV2, HaalCentraalVersion
from ..models import HaalCentraalConfig


class HaalCentraalModelTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUpTestData`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: HaalCentraalVersion | None = None

    # set in setUP
    service: Service | None = None
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

    def build_client_test(self):
        client = self.config.build_client()
        self.assertIsInstance(client, self.client)

    def get_attributes_test(self):
        attributes = self.config.get_attributes()
        self.assertEqual(attributes, self.attributes)


class HaalCentraalModelV1Tests(HaalCentraalModelTests, TestCase):
    version = HaalCentraalVersion.haalcentraal13

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_build_client(self):
        self.client = HaalCentraalV1Client
        super().build_client_test()

    def test_get_attributes(self):
        self.attributes = Attributes
        super().get_attributes_test()


class HaalCentraalModelV2Tests(HaalCentraalModelTests, TestCase):
    version = HaalCentraalVersion.haalcentraal20

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_build_client(self):
        self.client = HaalCentraalV2Client
        super().build_client_test()

    def test_get_attributes(self):
        self.attributes = AttributesV2
        super().get_attributes_test()


class HaalCentraalModelNoServiceTests(HaalCentraalModelTests, TestCase):
    def test_build_client(self):
        self.client = type(None)
        super().build_client_test()

    def test_get_attributes(self):
        self.attributes = Attributes
        super().get_attributes_test()
