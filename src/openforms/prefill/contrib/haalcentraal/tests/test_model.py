from unittest.mock import patch

from django.test import TestCase

from openforms.prefill.contrib.haalcentraal.client import (
    HaalCentraalV1Client,
    HaalCentraalV2Client,
)
from openforms.prefill.contrib.haalcentraal.constants import (
    Attributes,
    AttributesV2,
    HaalCentraalVersion,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..models import HaalCentraalConfig


class BaseHaalCentraalConfigTest:
    class HaalCentraalConfigTest(TestCase):
        def test_build_client(self):
            self.assertIsInstance(
                HaalCentraalConfig.get_solo().build_client(), self.client
            )

        def test_get_attributes(self):
            self.assertEqual(
                HaalCentraalConfig.get_solo().get_attributes(), self.attributes
            )


class HaalCentraalConfigV1Test(BaseHaalCentraalConfigTest.HaalCentraalConfigTest):
    def setUp(self):
        super().setUp()
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.models.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
                version=HaalCentraalVersion.haalcentraal13,
            ),
        )

        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = HaalCentraalV1Client
        self.attributes = Attributes


class HaalCentraalConfigV2Test(BaseHaalCentraalConfigTest.HaalCentraalConfigTest):
    def setUp(self):
        super().setUp()
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.models.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
                version=HaalCentraalVersion.haalcentraal20,
            ),
        )

        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = HaalCentraalV2Client
        self.attributes = AttributesV2


class BaseHaalCentraalNoConfigTest(BaseHaalCentraalConfigTest.HaalCentraalConfigTest):
    def setUp(self):
        super().setUp()
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.models.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(),
        )

        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = type(None)
        self.attributes = Attributes
