from typing import Literal
from unittest.mock import patch

from django.test import SimpleTestCase

from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..client import HaalCentraalClient, HaalCentraalV1Client, HaalCentraalV2Client
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
    version: HaalCentraalVersion | Literal[""]
    expected_client_class: type[HaalCentraalClient] | type[None]
    expected_attributes: type[Attributes] | type[AttributesV2]

    # set in setUp
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

    def test_build_client(self):
        client = self.config.build_client()

        self.assertIsInstance(client, self.expected_client_class)  # type: ignore

    def test_get_attributes(self):
        attributes = self.config.get_attributes()

        self.assertEqual(attributes, self.expected_attributes)  # type: ignore


class HaalCentraalModelV1Tests(HaalCentraalModelTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal13
    expected_client_class = HaalCentraalV1Client
    expected_attributes = Attributes

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()


class HaalCentraalModelV2Tests(HaalCentraalModelTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal20
    expected_client_class = HaalCentraalV2Client
    expected_attributes = AttributesV2

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()


class HaalCentraalModelNoServiceTests(HaalCentraalModelTests, SimpleTestCase):
    version = ""
    expected_client_class = type(None)
    expected_attributes = Attributes
