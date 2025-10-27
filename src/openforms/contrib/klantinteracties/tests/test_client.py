from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_klantinteracties_client
from ..models import KlantinteractiesConfig


class KlantinteractiesClientTest(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        config = KlantinteractiesConfig(
            service=ServiceFactory.build(
                api_root="http://localhost:8005/klantinteracties/api/v1/",
                api_type=APITypes.kc,
                header_key="Authorization",
                header_value="Token 9b17346dbb9493f967e6653bbcdb03ac2f7009fa",
                auth_type=AuthTypes.api_key,
            )
        )
        patcher = patch(
            "openforms.contrib.klantinteracties.client.KlantinteractiesConfig.get_solo",
            return_value=config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_digital_addresses(self):
        with get_klantinteracties_client() as client:
            data = client.get_digital_addresses_for_bsn(bsn="123456782")

        self.assertEqual(len(data), 5)

    def test_list_digital_addresses_empty(self):
        with get_klantinteracties_client() as client:
            data = client.get_digital_addresses_for_bsn(bsn="123456780")

        self.assertEqual(len(data), 0)
